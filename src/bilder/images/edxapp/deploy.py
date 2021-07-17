import os
import tempfile
from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, pip

from bilder.components.baseline.steps import service_configuration_watches
from bilder.components.hashicorp.consul.models import (
    Consul,
    ConsulConfig,
    ConsulService,
    ConsulServiceTCPCheck,
)
from bilder.components.hashicorp.consul.steps import proxy_consul_dns
from bilder.components.hashicorp.consul_template.models import (
    ConsulTemplate,
    ConsulTemplateConfig,
    ConsulTemplateTemplate,
    ConsulTemplateVaultConfig,
)
from bilder.components.hashicorp.consul_template.steps import (
    consul_template_permissions,
)
from bilder.components.hashicorp.steps import (
    configure_hashicorp_product,
    install_hashicorp_products,
    register_services,
)
from bilder.components.hashicorp.vault.models import (
    Vault,
    VaultAgentCache,
    VaultAgentConfig,
    VaultAutoAuthAWS,
    VaultAutoAuthConfig,
    VaultAutoAuthFileSink,
    VaultAutoAuthMethod,
    VaultAutoAuthSink,
    VaultConnectionConfig,
    VaultListener,
    VaultTemplate,
)
from bilder.components.hashicorp.vault.steps import vault_template_permissions
from bilder.facts import has_systemd  # noqa: F401
from bridge.lib.magic_numbers import VAULT_HTTP_PORT

VERSIONS = {  # noqa: WPS407
    "consul": "1.10.0",
    "vault": "1.7.3",
    "consul-template": "0.26.0",
}

WEB_NODE_TYPE = "web"
WORKER_NODE_TYPE = "worker"
node_type = host.data.node_type or os.environ.get("NODE_TYPE", WEB_NODE_TYPE)

# Install additional Python dependencies for use with edxapp
pip.packages(
    name="Install additional edX dependencies",
    packages=[
        "django-redis",  # Support for Redis caching in Django
        "celery-redbeat",  # Support for using Redis as the lock for Celery schedules
        "mitxpro-openedx-extensions==0.2.2",
        "social-auth-mitxpro==0.4",
        "edx-username-changer==0.1.0",
        "edx-sysadmin",
    ],
    present=True,
    virtualenv="/edx/app/edxapp/venvs/edxapp/",
    sudo_user="edxapp",
)

consul_configuration = {Path("00-default.json"): ConsulConfig()}
lms_config_path = Path("/edx/etc/lms.yml")
studio_config_path = Path("/edx/etc/studio.yml")
forum_config_path = Path("/edx/app/forum/forum_env")
lms_intermediate_template = Path("/etc/consul-template/templates/edxapp-lms.tmpl")
studio_intermediate_template = Path("/etc/consul-template/templates/edxapp-studio.tmpl")
forum_intermediate_template = Path("/etc/consul-template/templates/edx-forum.tmpl")
# Install Consul and Vault Agent
vault_templates = []
consul_templates = [
    ConsulTemplateTemplate(
        contents='{{ key "edxapp-template/studio" }}',
        destination=studio_intermediate_template,
    ),
    ConsulTemplateTemplate(
        source=studio_intermediate_template,
        destination=studio_config_path,
    ),
    ConsulTemplateTemplate(
        contents='{{ key "edxapp-template/lms" }}',
        destination=lms_intermediate_template,
    ),
    ConsulTemplateTemplate(
        source=lms_intermediate_template, destination=lms_config_path
    ),
]
if node_type == WEB_NODE_TYPE:
    vault_templates.extend(
        [
            VaultTemplate(
                contents=(
                    '{{ with secret "secret-mitxonline/mitxonline-wildcard-certificate" }}'  # noqa: E501
                    "{{ printf .Data.cert_chain }}{{ end }}"
                ),
                destination=Path("/etc/ssl/certs/edxapp.cert"),
            ),
            VaultTemplate(
                contents=(
                    '{{ with secret "secret-mitxonline/mitxonline-wildcard-certificate" }}'  # noqa: E501
                    "{{ printf .Data.key }}{{ end }}"
                ),
                destination=Path("/etc/ssl/certs/edxapp.key"),
            ),
        ]
    )
    consul_templates.extend(
        [
            ConsulTemplateTemplate(
                source=forum_intermediate_template, destination=forum_config_path
            ),
        ]
    )
    consul_configuration[Path("01-edxapp.json")] = ConsulConfig(
        services=[
            ConsulService(
                name="edxapp",
                port=8000,  # noqa: WPS432
                tags=["lms"],
                check=ConsulServiceTCPCheck(
                    name="edxapp-lms",
                    tcp="localhost:8000",
                    interval="10s",
                ),
            ),
            ConsulService(
                name="forum",
                port=4567,  # noqa: WPS432
                check=ConsulServiceTCPCheck(
                    name="edxapp-forum",
                    tcp="localhost:4567",
                    interval="10s",
                ),
            ),
        ]
    )

vault = Vault(
    version=VERSIONS["vault"],
    configuration=VaultAgentConfig(
        cache=VaultAgentCache(use_auto_auth_token="force"),  # noqa: S106
        listener=[
            VaultListener(
                type="tcp", address=f"127.0.0.1:{VAULT_HTTP_PORT}", tls_disable=True
            )
        ],
        vault=VaultConnectionConfig(
            address=f"https://vault.query.consul:{VAULT_HTTP_PORT}",
            tls_skip_verify=True,
        ),
        auto_auth=VaultAutoAuthConfig(
            method=VaultAutoAuthMethod(
                type="aws",
                mount_path="auth/aws",
                config=VaultAutoAuthAWS(role=f"edxapp-{node_type}"),
            ),
            sink=[VaultAutoAuthSink(type="file", config=[VaultAutoAuthFileSink()])],
        ),
        template=vault_templates,
    ),
)
consul = Consul(version=VERSIONS["consul"], configuration=consul_configuration)
consul_template = ConsulTemplate(
    version=VERSIONS["consul-template"],
    configuration={
        Path("00-default.json"): ConsulTemplateConfig(
            vault=ConsulTemplateVaultConfig(),
            template=consul_templates,
        )
    },
)
hashicorp_products = [vault, consul, consul_template]
install_hashicorp_products(hashicorp_products)
for product in hashicorp_products:
    configure_hashicorp_product(product)

# Upload templates for Vault agent
common_config = Path(__file__).parent.joinpath("templates", "common_values.yml")
studio_config = Path(__file__).parent.joinpath("templates", "studio_only.yml")
lms_config = Path(__file__).parent.joinpath("templates", "lms_only.yml")
forum_config = Path(__file__).parent.joinpath("templates", "forum.env")
with tempfile.NamedTemporaryFile("wt", delete=False) as studio_template:
    studio_template.write(common_config.read_text())
    studio_template.write(studio_config.read_text())
    files.put(
        name="Upload studio.yml template for Vault agent",
        src=studio_template.name,
        dest=studio_intermediate_template,
        user=consul_template.name,
        group=consul_template.name,
        create_remote_dir=True,
    )
with tempfile.NamedTemporaryFile("wt", delete=False) as lms_template:
    lms_template.write(common_config.read_text())
    lms_template.write(lms_config.read_text())
    files.put(
        name="Upload lms.yml template for consul-template agent",
        src=lms_template.name,
        dest=lms_intermediate_template,
        user=consul_template.name,
        group=consul_template.name,
        create_remote_dir=True,
    )
with tempfile.NamedTemporaryFile("wt", delete=False) as forum_template:
    forum_template.write(forum_config.read_text())
    files.put(
        name="Upload forum_env template for consul-template agent",
        src=forum_template.name,
        dest=forum_intermediate_template,
        user=consul_template.name,
        group=consul_template.name,
        create_remote_dir=True,
    )
vault_template_permissions(vault.configuration)
consul_template_permissions(consul_template.configuration)
# Manage services
if host.fact.has_systemd:
    register_services(hashicorp_products, start_services_immediately=False)
    service_configuration_watches(
        service_name="edxapp-lms",
        watched_files=[lms_config_path],
        start_now=False,
        onchange_command=(
            # Let edxapp read the rendered config file
            f"/bin/bash -c 'chown edxapp:www-data {lms_config_path} &&"  # noqa: WPS237, WPS221, E501
            # Ensure that Vault can update the file when credentials refresh
            f" setfacl -m u:consul-template:rwx {lms_config_path} &&"
            # Restart the edxapp process to reload the configuration file
            " /edx/bin/supervisorctl restart "
            f"{'lms' if node_type == WEB_NODE_TYPE else 'all'}'"
        ),
    )
    service_configuration_watches(
        service_name="edxapp-cms",
        watched_files=[studio_config_path],
        start_now=False,
        onchange_command=(
            # Let edxapp read the rendered config file
            f"/bin/bash -c 'chown edxapp:www-data {studio_config_path} &&"  # noqa: WPS237, WPS221, E501
            # Ensure that Vault can update the file when credentials refresh
            f" setfacl -m u:consul-template:rwx {studio_config_path} &&"
            # Restart the edxapp process to reload the configuration file
            " /edx/bin/supervisorctl restart "
            f"{'cms' if node_type == WEB_NODE_TYPE else 'all'}'"
        ),
    )
    service_configuration_watches(
        service_name="edxapp-forum",
        watched_files=[forum_config_path],
        start_now=False,
        onchange_command=(
            # Let edxapp read the rendered config file
            f"/bin/bash -c 'chown forum:www-data {forum_config_path} &&"  # noqa: WPS237, WPS221, E501
            # Ensure that Vault can update the file when credentials refresh
            f" setfacl -m u:consul-template:rwx {forum_config_path} &&"
            # Restart the edxapp process to reload the configuration file
            " /edx/bin/supervisorctl restart forum"
        ),
    )
    proxy_consul_dns()
