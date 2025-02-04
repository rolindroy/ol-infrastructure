from concourse.lib.constants import REGISTRY_IMAGE
from concourse.lib.models.pipeline import Identifier, RegistryImage, ResourceType


def rclone() -> ResourceType:
    return ResourceType(
        name=Identifier("rclone"),
        type=REGISTRY_IMAGE,
        source=RegistryImage(repository="mitodl/concourse-rclone-resource"),
    )


def packer_validate() -> ResourceType:
    return ResourceType(
        name=Identifier("packer-validator"),
        type=REGISTRY_IMAGE,
        source=RegistryImage(repository="mitodl/concourse-packer-resource"),
    )


def packer_build() -> ResourceType:
    return ResourceType(
        name=Identifier("packer-builder"),
        type=REGISTRY_IMAGE,
        source=RegistryImage(repository="mitodl/concourse-packer-resource-builder"),
    )


def ami_resource() -> ResourceType:
    return ResourceType(
        name=Identifier("amazon-ami"),
        type=REGISTRY_IMAGE,
        source=RegistryImage(repository="jdub/ami-resource"),
    )


def s3_sync() -> ResourceType:
    return ResourceType(
        name=Identifier("s3-sync"),
        type=REGISTRY_IMAGE,
        source=RegistryImage(repository="mitodl/concourse-s3-sync-resource"),
    )


def pulumi_provisioner_resource() -> ResourceType:
    return ResourceType(
        name=Identifier("pulumi-provisioner"),
        type=REGISTRY_IMAGE,
        source=RegistryImage(repository="mitodl/concourse-pulumi-resource-provisioner"),
    )
