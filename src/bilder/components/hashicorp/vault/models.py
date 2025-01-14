import abc
from collections.abc import Iterable
from pathlib import Path
from typing import Optional, Union

from pydantic import validator
from pydantic.types import conint

from bilder.components.hashicorp.models import (
    FlexibleBaseModel,
    HashicorpConfig,
    HashicorpProduct,
)


class VaultAutoAuthMethodConfig(FlexibleBaseModel, abc.ABC):
    pass


class VaultAutoAuthSinkConfig(FlexibleBaseModel, abc.ABC):
    pass


class VaultAutoAuthFileSink(VaultAutoAuthSinkConfig):
    path: Path = Path("/etc/vault/vault_agent_token")
    mode: Optional[int]


class VaultAutoAuthAppRole(VaultAutoAuthMethodConfig):
    role_id_file_path: Path
    secret_id_file_path: Optional[Path]
    remove_secret_id_file_after_reading: bool = True
    secret_id_response_wrapping_path: Optional[Path]


class VaultAutoAuthAWS(VaultAutoAuthMethodConfig):
    # The type of authentication; must be ec2 or iam.
    type: str = "iam"
    # The role to authenticate against on Vault.
    role: str
    # In seconds, how frequently the Vault agent should check for new credentials if
    # using the iam type.
    credential_poll_interval: Optional[int]
    access_key: Optional[str]
    secret_key: Optional[str]
    region: str = "us-east-1"
    session_token: Optional[str]
    header_value: Optional[str]


class VaultAutoAuthMethod(FlexibleBaseModel):
    type: str
    mount_path: Optional[str]
    namespace: Optional[str]
    wrap_ttl: Optional[Union[str, int]]
    config: VaultAutoAuthMethodConfig


class VaultAutoAuthSink(FlexibleBaseModel):
    type: str
    wrap_ttl: Optional[Union[str, int]]
    dh_type: Optional[str]
    dh_path: Optional[Path]
    derive_key: bool = False
    aad: Optional[str]
    aad_env_var: Optional[str]
    config: list[VaultAutoAuthSinkConfig]


class VaultAgentCache(FlexibleBaseModel):
    use_auto_auth_token: Union[str, bool] = True


class VaultAwsKmsSealConfig(FlexibleBaseModel):
    region: Optional[str] = "us-east-1"
    access_key: Optional[str]
    secret_key: Optional[str]
    kms_key_id: Optional[str]
    endpoint: Optional[str]
    session_token: Optional[str]


class VaultSealConfig(FlexibleBaseModel):
    awskms: Optional[VaultAwsKmsSealConfig]


class VaultTelemetryConfig(FlexibleBaseModel):
    usage_gauge_period: Optional[str]
    maximum_gauge_cardinality: Optional[int]
    disable_hostname: bool = False
    enable_hostname_label: bool = False


class ConsulStorageBackend(FlexibleBaseModel):
    address: Optional[str]
    check_timeout: Optional[str] = "5s"
    consistency_mode: Optional[str] = "default"
    disable_registration: bool = False
    max_parallel: Optional[str]
    path: Optional[str] = "vault/"
    scheme: Optional[str] = "http"
    service: Optional[str] = "vault"
    service_tags: Optional[str]
    token: Optional[str]
    session_ttl: Optional[str] = "15s"
    tls_ca_file: Optional[Path]
    tls_cert_file: Optional[Path]
    tls_key_file: Optional[Path]
    tls_min_version: Optional[str] = "tls12"


class VaultRetryJoin(FlexibleBaseModel):
    leader_api_addr: Optional[str]
    auto_join: Optional[str]
    auto_join_scheme: Optional[str]
    auto_join_port: Optional[int]
    leader_tls_servername: Optional[str]
    leader_ca_cert_file: Optional[Path]
    leader_client_cert_file: Optional[Path]
    leader_client_key_file: Optional[Path]
    leader_ca_cert: Optional[str]
    leader_client_cert: Optional[str]
    leader_client_key: Optional[str]


class IntegratedRaftStorageBackend(FlexibleBaseModel):
    path: Path = Path("/var/lib/vault/raft/")
    performance_multiplier: Optional[conint(ge=0, le=10)]  # type: ignore
    # The node_id is an optional parameter that will receive an autogenerated UUID if
    # not set.
    # https://github.com/hashicorp/vault/blob/master/physical/raft/raft.go#L289-L329
    node_id: Optional[str]
    trailing_logs: Optional[int]
    snapshot_threshold: Optional[int]
    retry_join: Optional[list[VaultRetryJoin]]
    max_entry_size: Optional[int]
    autopilot_reconcile_interval: Optional[str]


class VaultStorageBackend(FlexibleBaseModel):
    """Container class for holding named references to storage implementations.

    In order to add support for configuring an additional storage backend, the name of
    the backend as defined by Vault is set as the attribute name, and the type of the
    attribute is Optional[<NameOfStorageClass>].  This allows us to pass an instance of
    that class object to the associated attribute so that the rendered JSON is of the
    form

    {"storage": {"raft": {"path": "/data/storage/path"}}}
    """

    consul: Optional[ConsulStorageBackend]
    raft: Optional[IntegratedRaftStorageBackend]


class VaultAutoAuthConfig(FlexibleBaseModel):
    method: VaultAutoAuthMethod
    sink: Optional[list[VaultAutoAuthSink]]


class VaultConnectionConfig(FlexibleBaseModel):
    address: str
    ca_cert: Optional[Path]
    ca_path: Optional[Path]
    client_cert: Optional[Path]
    client_key: Optional[Path]
    tls_skip_verify: bool = False
    tls_server_name: Optional[str]


class VaultTemplate(FlexibleBaseModel):
    source: Optional[Path]
    contents: Optional[str]
    destination: Path
    create_dest_dirs: bool = True
    command: Optional[str]


class VaultTelemetryListener(FlexibleBaseModel):
    unauthenticated_metrics_access: bool = False


class VaultTCPListener(FlexibleBaseModel):
    address: Optional[str]
    cluster_address: Optional[str]
    http_idle_timeout: Optional[str]
    http_read_header_timeout: Optional[str]
    http_read_timeout: Optional[str]
    http_write_timeout: Optional[str]
    max_request_size: Optional[int]
    max_request_duration: Optional[str]
    tls_disable: Optional[bool]
    tls_cert_file: Optional[Path]
    tls_key_file: Optional[Path]
    tls_min_version: Optional[str]
    telemetry: Optional[VaultTelemetryListener]


class VaultListener(FlexibleBaseModel):
    tcp: Optional[VaultTCPListener]


class ConsulServiceRegistration(FlexibleBaseModel):
    address: Optional[str]  # address of Consul agent to communicate with
    check_timeout: Optional[str]
    disable_registration: str = "false"
    scheme: Optional[str] = "http"
    service: Optional[str] = "vault"
    service_tags: Optional[list[str]]
    service_address: Optional[str] = ""
    token: Optional[str]  # Consul ACL token to authorize setting the service definition
    tls_ca_file: Optional[Path]
    tls_cert_file: Optional[Path]
    tls_key_file: Optional[Path]
    tls_min_version: Optional[str]
    tls_skip_verify: Optional[bool]


class VaultServiceRegistration(FlexibleBaseModel):
    consul: Optional[ConsulServiceRegistration]


class VaultAgentConfig(HashicorpConfig):
    vault: Optional[VaultConnectionConfig]
    auto_auth: Optional[VaultAutoAuthConfig]
    cache: Optional[VaultAgentCache] = VaultAgentCache()
    pid_file: Optional[Path]
    exit_after_auth: bool = False
    template: Optional[list[VaultTemplate]]
    listener: Optional[list[VaultListener]]

    class Config:
        env_prefix = "vault_agent_"


class VaultServerConfig(HashicorpConfig):
    api_addr: Optional[str]
    cache_size: Optional[str]
    cluster_addr: Optional[str]
    cluster_name: Optional[str]
    default_lease_ttl: Optional[str]
    default_max_request_duration: Optional[str]
    disable_cache: bool = False
    disable_clustering: bool = False
    disable_mlock: bool = False
    ha_storage: Optional[list[VaultStorageBackend]]
    listener: Optional[list[VaultListener]]
    log_format: str = "json"
    log_level: str = "Warn"
    max_lease_ttl: Optional[str]
    plugin_directory: Optional[Path]
    seal: Optional[list[VaultSealConfig]]
    service_registration: Optional[VaultServiceRegistration]
    # Set storage as optional to allow for splitting into a separate config file
    storage: Optional[VaultStorageBackend]
    telemetry: Optional[VaultTelemetryConfig]
    ui: Optional[bool] = False

    class Config:
        env_prefix = "vault_"


class Vault(HashicorpProduct):
    _name: str = "vault"
    version: str = "1.8.0"
    configuration: dict[Path, HashicorpConfig] = {
        Path("vault.json"): VaultAgentConfig()
    }
    configuration_directory: Path = Path("/etc/vault/")
    data_directory: Path = Path("/var/lib/vault/")

    @validator("configuration")
    def validate_consistent_config_types(cls, configuration):
        type_set = {type(config_obj) for config_obj in configuration.values()}
        if len(type_set) > 1:
            raise ValueError("There are server and agent configuration objects present")
        return configuration

    def operating_mode(self) -> str:
        mode_map = {VaultAgentConfig: "agent", VaultServerConfig: "server"}
        return mode_map[{type(conf) for conf in self.configuration.values()}.pop()]

    @property
    def systemd_template_context(self):
        context_dict = {
            "mode": self.operating_mode(),
            "configuration_directory": self.configuration_directory,
        }
        if self.operating_mode() == "agent":
            context_dict["configuration_file"] = list(self.configuration.keys())[0]
        return context_dict

    def render_configuration_files(self) -> Iterable[tuple[Path, str]]:
        for fpath, config in self.configuration.items():
            yield self.configuration_directory.joinpath(fpath), config.json(
                exclude_none=True, indent=2
            )
