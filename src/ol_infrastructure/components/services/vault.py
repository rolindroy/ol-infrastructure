"""
This module controls mounting and configuration of database secret backends in Vault.

This includes:
- Mount a database backend at the configured mount point
- Set the configuration according to the requirements of the backend type
- Control the lease TTL settings
- Define the base set of roles according to our established best practices
"""
import json
from enum import Enum
from typing import Dict, Text, Union

from pulumi import ComponentResource, Output, ResourceOptions
from pulumi_vault import AuthBackend, Mount, Policy, approle, aws, database
from pydantic import BaseModel, validator

from ol_infrastructure.lib.vault import mysql_sql_statements, postgres_sql_statements

DEFAULT_PORT_POSTGRES = 5432
DEFAULT_PORT_MYSQL = 3306
DEFAULT_POT_MONGODB = 27017
SIX_MONTHS = 60 * 60 * 24 * 30 * 6  # noqa: WPS432


class DBEngines(str, Enum):  # noqa: WPS600
    """Constraints for valid engine types that are supported by this component."""

    postgres = "postgresql"
    mariadb = "mysql"
    mysql = "mysql"
    mysql_rds = "mysql_rds"
    mongodb = "mongodb"


class OLVaultDatabaseConfig(BaseModel):
    """Configuration object for Vault database backend resource."""

    db_name: Text
    mount_point: Text
    db_admin_username: Text
    db_admin_password: Text
    verify_connection: bool = True
    db_host: Union[Text, Output[Text]]
    max_ttl: int = SIX_MONTHS
    default_ttl: int = SIX_MONTHS

    class Config:  # noqa: WPS431, D106
        arbitrary_types_allowed = True


class OLVaultPostgresDatabaseConfig(OLVaultDatabaseConfig):
    """Configuration object for Postgres database to register with Vault."""

    db_port: int = DEFAULT_PORT_POSTGRES
    # The db_connection strings are passed through the `.format` method so the variables that need to remain in the
    # template to be passed to Vault are wrapped in 4 pairs of braces. TMM 2020-09-01
    db_connection: Text = (
        "postgresql://{{{{username}}}}:{{{{password}}}}@{db_host}:{db_port}/{db_name}"
    )
    db_type: Text = DBEngines.postgres.value
    role_statements: Dict[Text, Dict[Text, Text]] = postgres_sql_statements


class OLVaultMysqlDatabaseConfig(OLVaultDatabaseConfig):
    """Configuration object for MySQL/MariaDB database to register with Vault."""

    db_port: int = DEFAULT_PORT_MYSQL
    db_connection: Text = "{{{{username}}}}:{{{{password}}}}@tcp({db_host}:{db_port})/"
    db_type: Text = DBEngines.mysql_rds.value
    role_statements: Dict[Text, Dict[Text, Text]] = mysql_sql_statements


class OLVaultDatabaseBackend(ComponentResource):
    """Resource for encapsulating the steps needed to connect Vault to a database."""

    def __init__(
        self,
        db_config: Union[OLVaultMysqlDatabaseConfig, OLVaultPostgresDatabaseConfig],
        opts: ResourceOptions = None,
    ):
        super().__init__(
            "ol:services:Vault:DatabaseBackend", db_config.db_name, None, opts
        )

        resource_opts = ResourceOptions.merge(ResourceOptions(parent=self), opts)  # type: ignore

        self.db_mount = Mount(
            f"{db_config.db_name}-mount-point",
            opts=resource_opts,
            path=db_config.mount_point,
            type="database",
            max_lease_ttl_seconds=db_config.max_ttl,
            default_lease_ttl_seconds=db_config.default_ttl,
        )

        if isinstance(db_config.db_host, Output):
            connection_url: Union[Text, Output[Text]] = db_config.db_host.apply(
                lambda host: db_config.db_connection.format_map(
                    {
                        "db_port": db_config.db_port,
                        "db_name": db_config.db_name,
                        "db_host": host,
                    }
                )
            )
        else:
            connection_url = db_config.db_connection.format_map(
                {
                    "db_port": db_config.db_port,
                    "db_name": db_config.db_name,
                    "db_host": db_config.db_host,
                }
            )
        self.db_connection = database.SecretBackendConnection(
            f"{db_config.db_name}-database-connection",
            opts=resource_opts.merge(ResourceOptions(parent=self.db_mount)),  # type: ignore
            backend=db_config.mount_point,
            verify_connection=db_config.verify_connection,
            allowed_roles=sorted(db_config.role_statements.keys()),
            name=db_config.db_name,
            data={
                "username": db_config.db_admin_username,
                "password": db_config.db_admin_password,
            },
            **{db_config.db_type: {"connection_url": connection_url}},
        )

        self.db_roles = {}
        for role_name, role_defs in db_config.role_statements.items():
            self.db_roles[role_name] = database.SecretBackendRole(
                f"{db_config.db_name}-database-role-{role_name}",
                opts=resource_opts.merge(ResourceOptions(parent=self.db_connection)),  # type: ignore
                name=role_name,
                backend=self.db_mount.path,
                db_name=db_config.db_name,
                creation_statements=[
                    role_defs["create"].format(role_name=db_config.db_name)
                ],
                revocation_statements=[
                    role_defs["revoke"].format(role_name=db_config.db_name)
                ],
                max_ttl=db_config.max_ttl,
                default_ttl=db_config.default_ttl,
            )
        self.register_outputs({})


class OLVaultAWSSecretsEngineConfig(BaseModel):
    app_name: Text
    aws_access_key: Text
    default_lease_ttl_seconds: int = SIX_MONTHS
    max_lease_ttl_seconds: int = SIX_MONTHS
    description: Text
    aws_secret_key: Text
    vault_backend_path: Text
    policy_documents: Dict[Text, Text]
    credential_type: Text = "iam_user"

    @validator("vault_backend_path")
    def is_valid_path(
        cls: "OLVaultAWSSecretsEngineConfig", vault_backend_path: Text  # noqa: N805
    ) -> Text:
        if vault_backend_path.startswith("/") or vault_backend_path.endswith("/"):
            raise ValueError(
                f"The specified path value {vault_backend_path} can not start or end with a slash"
            )
        return vault_backend_path


class OLVaultAWSSecretsEngine(ComponentResource):
    def __init__(
        self, engine_config: OLVaultAWSSecretsEngineConfig, opts: ResourceOptions = None
    ):
        super().__init__(
            "ol:services:Vault:AWSSecretsEngine", engine_config.app_name, None, opts
        )

        resource_options = ResourceOptions(parent=self).merge(opts)  # type: ignore

        self.aws_secrets_engine = aws.SecretBackend(
            # TODO verify app_name exists based on Apps class in ol_types
            f"aws-{engine_config.app_name}",
            access_key=engine_config.aws_access_key,
            secret_key=engine_config.aws_secret_key,
            path=f"aws-{engine_config.vault_backend_path}",
            opts=resource_options,
        )

        for role_name, policy in engine_config.policy_documents.items():
            aws.SecretBackendRole(
                role_name,
                backend=self.aws_secrets_engine.name,
                credential_type=engine_config.credential_type,
                name=role_name,
                policy_document=json.dumps(policy),
                opts=resource_options,
            )

        self.register_outputs({})


class OLVaultAppRoleAuthBackendConfig(BaseModel):
    authbackend_name: Text
    backend_type: str = "approle"
    description: Text
    role_name: Text
    token_policies: Dict[str, str]


class OLVaultAppRoleAuthBackend(ComponentResource):
    """Register an App Role with Vault as an authentication option."""

    # Due to the following open issue https://github.com/pulumi/pulumi-vault/issues/10
    # we can't pass json as policy and thus had to do some workarounds below. Those can
    # changed once that issue is resolved.
    def __init__(
        self,
        approle_config: OLVaultAppRoleAuthBackendConfig,
        opts: ResourceOptions = None,
    ):
        super().__init__(
            "ol:services:Vault:AppRoleAuthBackend",
            approle_config.authbackend_name,
            None,
            opts,
        )

        resource_options = ResourceOptions(parent=self).merge(opts)  # type: ignore

        self.approle_backend = AuthBackend(
            approle_config.authbackend_name,
            description=approle_config.description,
            path=approle_config.authbackend_name,
            type=approle_config.backend_type,
            opts=resource_options,
        )

        token_policy_names = []
        for policy_key, policy_value in approle_config.token_policies.items():
            vault_policy = Policy(policy_key, policy=policy_value)
            token_policy_names.append(vault_policy.name)

        self.approle_backend_role = approle.AuthBackendRole(
            approle_config.authbackend_name,
            backend=self.approle_backend.path,
            role_name=approle_config.role_name,
            token_policies=token_policy_names,
            opts=resource_options,
        )

        self.register_outputs({})
