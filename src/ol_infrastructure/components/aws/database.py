"""This module defines a Pulumi component resource for encapsulating our best practices for building RDS instances.

This includes:

- Create a parameter group for the database
- Create and configure a backup policy
- Manage the root user password
- Create relevant security groups
- Create DB instance
"""
from enum import Enum
from typing import Optional, Union

import pulumi
from pulumi_aws import rds
from pulumi_aws.ec2 import SecurityGroup
from pydantic import BaseModel, PositiveInt, SecretStr, conint, validator

from ol_infrastructure.lib.aws.rds_helper import (
    DBInstanceTypes,
    db_engines,
    parameter_group_family,
)
from ol_infrastructure.lib.ol_types import AWSBase

MAX_BACKUP_DAYS = 35


class StorageType(str, Enum):
    """Container for constraining available selection of storage types."""

    magnetic = "standard"
    ssd = "gp2"
    performance = "io1"


class OLReplicaDBConfig(BaseModel):
    """Configuration object for defining configuration needed to create a read replica."""

    instance_size: str = "db.t3.small"
    storage_type: StorageType = StorageType.ssd
    public_access: bool = False
    security_groups: Optional[list[SecurityGroup]] = None

    class Config:
        arbitrary_types_allowed = True


class OLDBConfig(AWSBase):
    """Configuration object for defining the interface to create an RDS instance with sane defaults."""

    engine: str
    engine_version: str
    instance_name: str  # The name of the RDS instance
    password: SecretStr
    parameter_overrides: list[dict[str, Union[str, bool, int, float]]]
    port: PositiveInt
    subnet_group_name: Union[str, pulumi.Output[str]]
    security_groups: list[SecurityGroup]
    backup_days: conint(ge=0, le=MAX_BACKUP_DAYS, strict=True) = 30  # type: ignore
    db_name: Optional[str] = None  # The name of the database schema to create
    instance_size: str = DBInstanceTypes.general_purpose_large.value
    max_storage: Optional[PositiveInt] = None  # Set to allow for storage autoscaling
    multi_az: bool = True
    prevent_delete: bool = True
    public_access: bool = False
    take_final_snapshot: bool = True
    storage: PositiveInt = PositiveInt(50)
    storage_type: StorageType = StorageType.ssd
    username: str = "oldevops"
    read_replica: Optional[OLReplicaDBConfig] = None

    class Config:
        arbitrary_types_allowed = True

    @validator("engine")
    def is_valid_engine(cls: "OLDBConfig", engine: str) -> str:
        valid_engines = db_engines()
        if engine not in valid_engines:
            raise ValueError("The specified DB engine is not a valid option in AWS.")
        return engine

    @validator("engine_version")
    def is_valid_version(cls: "OLDBConfig", engine_version: str, values: dict) -> str:
        engine: str = values.get("engine")  # type: ignore
        engines_map = db_engines()
        if engine_version not in engines_map.get(engine, []):
            raise ValueError(
                f"The specified version of the {engine} engine is not supported in AWS."
            )
        return engine_version


class OLPostgresDBConfig(OLDBConfig):
    """Configuration container to specify settings specific to Postgres."""

    engine: str = "postgres"
    engine_version: str = "13.4"
    port: PositiveInt = PositiveInt(5432)
    parameter_overrides: list[dict[str, Union[str, bool, int, float]]] = [
        {"name": "client_encoding", "value": "UTF-8"},
        {"name": "timezone", "value": "UTC"},
        {"name": "rds.force_ssl", "value": 1},
        {"name": "autovacuum", "value": 1},
    ]


class OLMariaDBConfig(OLDBConfig):
    """Configuration container to specify settings specific to MariaDB."""

    engine: str = "mariadb"
    engine_version: str = "10.5.13"
    port: PositiveInt = PositiveInt(3306)
    parameter_overrides: list[dict[str, Union[str, bool, int, float]]] = [
        {"name": "character_set_client", "value": "utf8mb4"},
        {"name": "character_set_connection", "value": "utf8mb4"},
        {"name": "character_set_database", "value": "utf8mb4"},
        {"name": "character_set_filesystem", "value": "utf8mb4"},
        {"name": "character_set_results", "value": "utf8mb4"},
        {"name": "character_set_server", "value": "utf8mb4"},
        {"name": "collation_server", "value": "utf8mb4_unicode_ci"},
        {"name": "collation_connection", "value": "utf8mb4_unicode_ci"},
        {"name": "time_zone", "value": "UTC"},
    ]


class OLAmazonDB(pulumi.ComponentResource):
    """Component to create an RDS instance with sane defaults and manage associated resources."""

    def __init__(self, db_config: OLDBConfig, opts: pulumi.ResourceOptions = None):
        """Create an RDS instance, parameter group, and optionally read replica.

        :param db_config: Configuration object for customizing the deployed database
            instance.
        :type db_config: OLDBConfig

        :param opts: Custom pulumi options to pass to child resources.
        :type opts: pulumi.ResourceOptions
        """
        super().__init__(
            "ol:infrastructure:aws:database:OLAmazonDB",
            db_config.instance_name,
            None,
            opts,
        )

        resource_options = pulumi.ResourceOptions(parent=self).merge(opts)  # type: ignore

        self.parameter_group = rds.ParameterGroup(
            f"{db_config.instance_name}-{db_config.engine}-parameter-group",
            family=parameter_group_family(db_config.engine, db_config.engine_version),
            opts=resource_options.merge(
                pulumi.ResourceOptions(ignore_changes=["family"])
            ),
            name=f"{db_config.instance_name}-{db_config.engine}-parameter-group",
            tags=db_config.tags,
            parameters=db_config.parameter_overrides,
        )

        self.db_instance = rds.Instance(
            f"{db_config.instance_name}-{db_config.engine}-instance",
            allocated_storage=db_config.storage,
            auto_minor_version_upgrade=True,
            backup_retention_period=db_config.backup_days,
            copy_tags_to_snapshot=True,
            db_subnet_group_name=db_config.subnet_group_name,
            deletion_protection=db_config.prevent_delete,
            engine=db_config.engine,
            engine_version=db_config.engine_version,
            final_snapshot_identifier=f"{db_config.instance_name}-{db_config.engine}-final-snapshot",
            identifier=db_config.instance_name,
            instance_class=db_config.instance_size,
            max_allocated_storage=db_config.max_storage,
            multi_az=db_config.multi_az,
            db_name=db_config.db_name,
            opts=resource_options.merge(
                pulumi.ResourceOptions(ignore_changes=["engine_version"])
            ),
            parameter_group_name=self.parameter_group.name,
            password=db_config.password.get_secret_value(),
            port=db_config.port,
            publicly_accessible=db_config.public_access,
            skip_final_snapshot=not db_config.take_final_snapshot,
            storage_encrypted=True,
            storage_type=db_config.storage_type.value,
            tags=db_config.tags,
            username=db_config.username,
            vpc_security_group_ids=[group.id for group in db_config.security_groups],
        )

        component_outputs = {
            "parameter_group": self.parameter_group,
            "rds_instance": self.db_instance,
        }

        if db_config.read_replica:
            self.db_replica = rds.Instance(
                f"{db_config.instance_name}-{db_config.engine}-replica",
                identifier=f"{db_config.instance_name}-replica",
                instance_class=db_config.read_replica.instance_size,
                kms_key_id=self.db_instance.kms_key_id,
                opts=resource_options,
                publicly_accessible=db_config.read_replica.public_access,
                replicate_source_db=self.db_instance.id,
                storage_type=db_config.read_replica.storage_type.value,
                tags=db_config.tags,
                vpc_security_group_ids=[
                    group.id
                    for group in db_config.read_replica.security_groups
                    or db_config.security_groups
                ],
            )
            component_outputs["rds_replica"] = self.db_replica

        self.register_outputs(component_outputs)
