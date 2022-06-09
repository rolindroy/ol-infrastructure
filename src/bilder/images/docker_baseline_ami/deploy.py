import os
from pathlib import Path

from pyinfra import host
from pyinfra.operations import server

from bilder.components.docker.docker_compose_steps import deploy_docker_compose
from bilder.components.docker.steps import deploy_docker
from bilder.components.hashicorp.consul.models import Consul, ConsulConfig
from bilder.components.hashicorp.consul.steps import proxy_consul_dns
from bilder.components.hashicorp.consul_template.models import ConsulTemplate
from bilder.components.hashicorp.steps import (
    configure_hashicorp_product,
    install_hashicorp_products,
    register_services,
)
from bilder.components.hashicorp.vault.models import (
    Vault,
    VaultAgentCache,
    VaultAgentConfig,
    VaultConnectionConfig,
    VaultListener,
    VaultTCPListener,
)
from bilder.components.hashicorp.vault.steps import vault_template_permissions
from bilder.components.vector.models import VectorConfig
from bilder.components.vector.steps import (
    configure_vector,
    install_vector,
    vector_service,
)
from bilder.facts.has_systemd import HasSystemd
from bridge.lib.magic_numbers import VAULT_HTTP_PORT
from bridge.lib.versions import CONSUL_TEMPLATE_VERSION, CONSUL_VERSION, VAULT_VERSION
from bridge.secrets.sops import set_env_secrets

VERSIONS = {
    "consul": os.environ.get("CONSUL_VERSION", CONSUL_VERSION),
    "vault": os.environ.get("VAULT_VERSION", VAULT_VERSION),
    "consul_template": os.environ.get(
        "CONSUL_TEMPLATE_VERSION", CONSUL_TEMPLATE_VERSION
    ),
}
TEMPLATES_DIRECTORY = Path(__file__).parent.joinpath("templates")
VECTOR_INSTALL_NAME = "vector-log"

# Set up configuration objects
set_env_secrets(Path("consul/consul.env"))

consul_configuration = {Path("00-default.json"): ConsulConfig()}
vector_config = VectorConfig(is_proxy=False)

vault_config = VaultAgentConfig(
    cache=VaultAgentCache(use_auto_auth_token="force"),
    listener=[
        VaultListener(
            tcp=VaultTCPListener(
                address=f"127.0.0.1:{VAULT_HTTP_PORT}", tls_disable=True
            )
        )
    ],
    vault=VaultConnectionConfig(
        address=f"https://active.vault.service.consul:{VAULT_HTTP_PORT}",
        tls_skip_verify=True,
    ),
)
vault = Vault(
    version=VERSIONS["vault"],
    configuration={Path("vault.json"): vault_config},
)
consul = Consul(version=VERSIONS["consul"], configuration=consul_configuration)
consul_template_config = ConsulTemplate()

hashicorp_products = [vault, consul, consul_template_config]
install_hashicorp_products(hashicorp_products)


# # Install vector
# vector_config.configuration_templates[
#     TEMPLATES_DIRECTORY.joinpath("vector", "vector-log-proxy.yaml.j2")
# ] = {}

install_vector(vector_config)
vault_template_permissions(vault_config)
configure_vector(vector_config)
vector_service(vector_config)

for product in hashicorp_products:
    configure_hashicorp_product(product)


deploy_docker()
deploy_docker_compose()

if host.get_fact(HasSystemd):
    register_services(hashicorp_products, start_services_immediately=False)
    proxy_consul_dns()
    server.service(
        name="Ensure docker service is running",
        service="docker",
        running=True,
        enabled=True,
    )
    server.service(
        name="Ensure docker compose service is enabled",
        service="docker-compose",
        running=False,
        enabled=True,
    )