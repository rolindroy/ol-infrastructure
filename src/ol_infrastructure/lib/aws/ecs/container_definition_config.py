from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


def build_container_log_options(
    service_name: str,
    task_name: str,
    container_name: Optional[str] = None,
) -> Dict[str, str]:
    return {
        "awslogs-group": f"ecs/{service_name}/{task_name}/",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": f"{container_name}",
        "awslogs-create-group": "true",
    }


class RepositoryCredentials(BaseModel):
    """
    The private repository authentication credentials to use.
    """

    credentials_parameter: str = Field(
        ...,
        alias="credentialsParameter",
        description=(
            "The Amazon Resource Name (ARN) of the secret containing the private"
            " repository credentials.  When you are using the Amazon ECS API, AWS CLI,"
            " or AWS SDK, if the secret exists in the same Region as the task that you"
            " are launching then you can use either the full ARN or the name of the"
            " secret. When you are using the AWS Management Console, you must specify"
            " the full ARN of the secret. "
        ),
    )


class Protocol(Enum):
    """The protocol used for the port mapping. The default is tcp."""

    tcp = "tcp"
    udp = "udp"


class PortMapping(BaseModel):
    container_port: Optional[int] = Field(
        None,
        alias="containerPort",
        description=(
            "The port number on the container that is bound to the user-specified or"
            " automatically assigned host port. If you are using containers in a task"
            " with the awsvpc or host network mode, exposed ports should be specified"
            " using containerPort. If you are using containers in a task with the"
            " bridge network mode and you specify a container port and not a host port,"
            " your container automatically receives a host port in the ephemeral port"
            " range. For more information, see hostPort. Port mappings that are"
            " automatically assigned in this way do not count toward the 100 reserved"
            " ports limit of a container instance.  You cannot expose the same"
            " container port for multiple protocols. An error will be returned if this"
            " is attempted. "
        ),
    )
    host_port: Optional[int] = Field(
        None,
        alias="hostPort",
        description=(
            "The port number on the container instance to reserve for your container."
            " If you are using containers in a task with the awsvpc or host network"
            " mode, the hostPort can either be left blank or set to the same value as"
            " the containerPort. If you are using containers in a task with the bridge"
            " network mode, you can specify a non-reserved host port for your container"
            " port mapping, or you can omit the hostPort (or set it to 0) while"
            " specifying a containerPort and your container automatically receives a"
            " port in the ephemeral port range for your container instance operating"
            " system and Docker version. The default ephemeral port range for Docker"
            " version 1.6.0 and later is listed on the instance under"
            " /proc/sys/net/ipv4/ip_local_port_range. If this kernel parameter is"
            " unavailable, the default ephemeral port range from 49153 through 65535 is"
            " used. Do not attempt to specify a host port in the ephemeral port range"
            " as these are reserved for automatic assignment. In general, ports below"
            " 32768 are outside of the ephemeral port range.  The default ephemeral"
            " port range from 49153 through 65535 is always used for Docker versions"
            " before 1.6.0.  The default reserved ports are 22 for SSH, the Docker"
            " ports 2375 and 2376, and the Amazon ECS container agent ports"
            " 51678-51680. Any host port that was previously specified in a running"
            " task is also reserved while the task is running (after a task stops, the"
            " host port is released). The current reserved ports are displayed in the"
            " remainingResources of DescribeContainerInstances output. A container"
            " instance can have up to 100 reserved ports at a time, including the"
            " default reserved ports. Automatically assigned ports don't count toward"
            " the 100 reserved ports limit."
        ),
    )
    protocol: Optional[Protocol] = Field(
        Protocol.tcp,
        description=(
            "The protocol used for the port mapping. Valid values are tcp and udp. The"
            " default is tcp."
        ),
    )


class EnvironmentItem(BaseModel):
    name: Optional[str] = Field(
        None,
        description=(
            "The name of the key-value pair. For environment variables, this is the"
            " name of the environment variable."
        ),
    )
    environment_value: Optional[str] = Field(
        None,
        alias="value",
        description=(
            "The value of the key-value pair. For environment variables, this is the"
            " value of the environment variable."
        ),
    )


class EnvironmentFile(BaseModel):
    object_arn: str = Field(
        ...,
        alias="value",
        description=(
            "The Amazon Resource Name (ARN) of the Amazon S3 object containing the"
            " environment variable file."
        ),
    )
    type: Literal["s3"] = Field(
        ..., description="The file type to use. The only supported value is s3."
    )


class MountPoint(BaseModel):
    source_volume: Optional[str] = Field(
        None,
        alias="sourceVolume",
        description=(
            "The name of the volume to mount. Must be a volume name referenced in the"
            " name parameter of task definition volume."
        ),
    )
    container_path: Optional[str] = Field(
        None,
        alias="containerPath",
        description="The path on the container to mount the host volume at.",
    )
    read_only: Optional[bool] = Field(
        None,
        alias="readOnly",
        description=(
            "If this value is true, the container has read-only access to the volume."
            " If this value is false, then the container can write to the volume. The"
            " default value is false."
        ),
    )


class VolumesFromItem(BaseModel):
    source_container: Optional[str] = Field(
        None,
        alias="sourceContainer",
        description=(
            "The name of another container within the same task definition from which"
            " to mount volumes."
        ),
    )
    read_only: Optional[bool] = Field(
        None,
        alias="readOnly",
        description=(
            "If this value is true, the container has read-only access to the volume."
            " If this value is false, then the container can write to the volume. The"
            " default value is false."
        ),
    )


class Capabilities(BaseModel):
    """
    The Linux capabilities for the container that are added to or dropped from the
    default configuration provided by Docker.  For tasks that use the Fargate launch
    type, capabilities is supported for all platform versions but the add parameter is
    only supported if using platform version 1.4.0 or later.
    """

    add: Optional[List[str]] = Field(
        None,
        description=(
            "The Linux capabilities for the container that have been added to the"
            " default configuration provided by Docker. This parameter maps to CapAdd"
            " in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --cap-add option to https://docs.docker.com/engine/reference/run/ docker"
            " run.  The SYS_PTRACE capability is supported for tasks that use the"
            " Fargate launch type if they are also using platform version 1.4.0. The"
            " other capabilities are not supported for any platform versions.  Valid"
            ' values: "ALL" | "AUDIT_CONTROL" | "AUDIT_WRITE" | "BLOCK_SUSPEND" |'
            ' "CHOWN" | "DAC_OVERRIDE" | "DAC_READ_SEARCH" | "FOWNER" | "FSETID" |'
            ' "IPC_LOCK" | "IPC_OWNER" | "KILL" | "LEASE" | "LINUX_IMMUTABLE" |'
            ' "MAC_ADMIN" | "MAC_OVERRIDE" | "MKNOD" | "NET_ADMIN" | "NET_BIND_SERVICE"'
            ' | "NET_BROADCAST" | "NET_RAW" | "SETFCAP" | "SETGID" | "SETPCAP" |'
            ' "SETUID" | "SYS_ADMIN" | "SYS_BOOT" | "SYS_CHROOT" | "SYS_MODULE" |'
            ' "SYS_NICE" | "SYS_PACCT" | "SYS_PTRACE" | "SYS_RAWIO" | "SYS_RESOURCE" |'
            ' "SYS_TIME" | "SYS_TTY_CONFIG" | "SYSLOG" | "WAKE_ALARM" '
        ),
    )
    drop: Optional[List[str]] = Field(
        None,
        description=(
            "The Linux capabilities for the container that have been removed from the"
            " default configuration provided by Docker. This parameter maps to CapDrop"
            " in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --cap-drop option to https://docs.docker.com/engine/reference/run/ docker"
            ' run. Valid values: "ALL" | "AUDIT_CONTROL" | "AUDIT_WRITE" |'
            ' "BLOCK_SUSPEND" | "CHOWN" | "DAC_OVERRIDE" | "DAC_READ_SEARCH" | "FOWNER"'
            ' | "FSETID" | "IPC_LOCK" | "IPC_OWNER" | "KILL" | "LEASE" |'
            ' "LINUX_IMMUTABLE" | "MAC_ADMIN" | "MAC_OVERRIDE" | "MKNOD" | "NET_ADMIN"'
            ' | "NET_BIND_SERVICE" | "NET_BROADCAST" | "NET_RAW" | "SETFCAP" | "SETGID"'
            ' | "SETPCAP" | "SETUID" | "SYS_ADMIN" | "SYS_BOOT" | "SYS_CHROOT" |'
            ' "SYS_MODULE" | "SYS_NICE" | "SYS_PACCT" | "SYS_PTRACE" | "SYS_RAWIO" |'
            ' "SYS_RESOURCE" | "SYS_TIME" | "SYS_TTY_CONFIG" | "SYSLOG" | "WAKE_ALARM" '
        ),
    )


class Permission(Enum):
    read = "read"
    write = "write"
    mknod = "mknod"


class Device(BaseModel):
    host_path: str = Field(
        ...,
        alias="hostPath",
        description="The path for the device on the host container instance.",
    )
    container_path: Optional[str] = Field(
        None,
        alias="containerPath",
        description="The path inside the container at which to expose the host device.",
    )
    permissions: Optional[List[Permission]] = Field(
        None,
        description=(
            "The explicit permissions to provide to the container for the device. By"
            " default, the container has permissions for read, write, and mknod for the"
            " device."
        ),
    )


class Tmpfs(BaseModel):
    container_path: str = Field(
        ...,
        alias="containerPath",
        description="The absolute file path where the tmpfs volume is to be mounted.",
    )
    size: int = Field(..., description="The size (in MiB) of the tmpfs volume.")
    mount_options: Optional[List[str]] = Field(
        None,
        alias="mountOptions",
        description=(
            'The list of tmpfs volume mount options. Valid values: "defaults" | "ro" |'
            ' "rw" | "suid" | "nosuid" | "dev" | "nodev" | "exec" | "noexec" | "sync" |'
            ' "async" | "dirsync" | "remount" | "mand" | "nomand" | "atime" | "noatime"'
            ' | "diratime" | "nodiratime" | "bind" | "rbind" | "unbindable" |'
            ' "runbindable" | "private" | "rprivate" | "shared" | "rshared" | "slave" |'
            ' "rslave" | "relatime" | "norelatime" | "strictatime" | "nostrictatime" |'
            ' "mode" | "uid" | "gid" | "nr_inodes" | "nr_blocks" | "mpol" '
        ),
    )


class LinuxParameters(BaseModel):
    """
    Linux-specific modifications that are applied to the container, such as Linux kernel
    capabilities.  For more information see KernelCapabilities.  This parameter is not
    supported for Windows containers.
    """

    capabilities: Optional[Capabilities] = Field(
        None,
        description=(
            "The Linux capabilities for the container that are added to or dropped from"
            " the default configuration provided by Docker.  For tasks that use the"
            " Fargate launch type, capabilities is supported for all platform versions"
            " but the add parameter is only supported if using platform version 1.4.0"
            " or later. "
        ),
    )
    devices: Optional[List[Device]] = Field(
        None,
        description=(
            "Any host devices to expose to the container. This parameter maps to"
            " Devices in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --device option to https://docs.docker.com/engine/reference/run/ docker"
            " run.  If you are using tasks that use the Fargate launch type, the"
            " devices parameter is not supported. "
        ),
    )
    init_process_enabled: Optional[bool] = Field(
        None,
        alias="initProcessEnabled",
        description=(
            "Run an init process inside the container that forwards signals and reaps"
            " processes. This parameter maps to the --init option to"
            " https://docs.docker.com/engine/reference/run/ docker run. This parameter"
            " requires version 1.25 of the Docker Remote API or greater on your"
            " container instance. To check the Docker Remote API version on your"
            " container instance, log in to your container instance and run the"
            " following command: sudo docker version --format '{{.Server.APIVersion}}' "
        ),
    )
    shared_memory_size: Optional[int] = Field(
        None,
        alias="sharedMemorySize",
        description=(
            "The value for the size (in MiB) of the /dev/shm volume. This parameter"
            " maps to the --shm-size option to"
            " https://docs.docker.com/engine/reference/run/ docker run.  If you are"
            " using tasks that use the Fargate launch type, the sharedMemorySize"
            " parameter is not supported. "
        ),
    )
    tmpfs: Optional[List[Tmpfs]] = Field(
        None,
        description=(
            "The container path, mount options, and size (in MiB) of the tmpfs mount."
            " This parameter maps to the --tmpfs option to"
            " https://docs.docker.com/engine/reference/run/ docker run.  If you are"
            " using tasks that use the Fargate launch type, the tmpfs parameter is not"
            " supported. "
        ),
    )
    max_swap: Optional[int] = Field(
        None,
        alias="maxSwap",
        description=(
            "The total amount of swap memory (in MiB) a container can use. This"
            " parameter will be translated to the --memory-swap option to"
            " https://docs.docker.com/engine/reference/run/ docker run where the value"
            " would be the sum of the container memory plus the maxSwap value. If a"
            " maxSwap value of 0 is specified, the container will not use swap."
            " Accepted values are 0 or any positive integer. If the maxSwap parameter"
            " is omitted, the container will use the swap configuration for the"
            " container instance it is running on. A maxSwap value must be set for the"
            " swappiness parameter to be used.  If you are using tasks that use the"
            " Fargate launch type, the maxSwap parameter is not supported. "
        ),
    )
    swappiness: Optional[int] = Field(
        None,
        description=(
            "This allows you to tune a container's memory swappiness behavior. A"
            " swappiness value of 0 will cause swapping to not happen unless absolutely"
            " necessary. A swappiness value of 100 will cause pages to be swapped very"
            " aggressively. Accepted values are whole numbers between 0 and 100. If the"
            " swappiness parameter is not specified, a default value of 60 is used. If"
            " a value is not specified for maxSwap then this parameter is ignored. This"
            " parameter maps to the --memory-swappiness option to"
            " https://docs.docker.com/engine/reference/run/ docker run.  If you are"
            " using tasks that use the Fargate launch type, the swappiness parameter is"
            " not supported. "
        ),
    )


class AwsContainerSecret(BaseModel):
    name: str = Field(..., description="The name of the secret.")
    value_from: str = Field(
        ...,
        alias="valueFrom",
        description=(
            "The secret to expose to the container. The supported values are either the"
            " full ARN of the AWS Secrets Manager secret or the full ARN of the"
            " parameter in the AWS Systems Manager Parameter Store.  If the AWS Systems"
            " Manager Parameter Store parameter exists in the same Region as the task"
            " you are launching, then you can use either the full ARN or name of the"
            " parameter. If the parameter exists in a different Region, then the full"
            " ARN must be specified. "
        ),
    )


class Condition(Enum):
    """
    The dependency condition of the container.  The following are the available
    conditions and their behavior: START - This condition emulates the behavior of links
    and volumes today.  It validates that a dependent container is started before
    permitting other containers to start.  COMPLETE - This condition validates that a
    dependent container runs to completion (exits) before permitting other containers to
    start.  This can be useful for nonessential containers that run a script and then
    exit.  SUCCESS - This condition is the same as COMPLETE, but it also requires that
    the container exits with a zero status.  HEALTHY - This condition validates that the
    dependent container passes its Docker health check before permitting other
    containers to start.  This requires that the dependent container has health checks
    configured.  This condition is confirmed only at task startup.
    """

    start = "START"
    complete = "COMPLETE"
    success = "SUCCESS"
    healthy = "HEALTHY"


class DependsOnItem(BaseModel):
    container_name: str = Field(
        ..., alias="containerName", description="The name of a container."
    )
    condition: Condition = Field(
        ...,
        description=(
            "The dependency condition of the container. The following are the available"
            " conditions and their behavior:    START - This condition emulates the"
            " behavior of links and volumes today. It validates that a dependent"
            " container is started before permitting other containers to start.   "
            " COMPLETE - This condition validates that a dependent container runs to"
            " completion (exits) before permitting other containers to start. This can"
            " be useful for nonessential containers that run a script and then exit.   "
            " SUCCESS - This condition is the same as COMPLETE, but it also requires"
            " that the container exits with a zero status.    HEALTHY - This condition"
            " validates that the dependent container passes its Docker health check"
            " before permitting other containers to start. This requires that the"
            " dependent container has health checks configured. This condition is"
            " confirmed only at task startup.  "
        ),
    )


class ExtraHost(BaseModel):
    hostname: str = Field(
        ..., description="The hostname to use in the /etc/hosts entry."
    )
    ip_address: str = Field(
        ...,
        alias="ipAddress",
        description="The IP address to use in the /etc/hosts entry.",
    )


class UlimitResource(Enum):
    """
    The type of the ulimit.
    """

    core = "core"
    cpu = "cpu"
    data = "data"  # noqa: WPS110
    fsize = "fsize"
    locks = "locks"
    memlock = "memlock"
    msgqueue = "msgqueue"
    nice = "nice"
    nofile = "nofile"
    nproc = "nproc"
    rss = "rss"
    rtprio = "rtprio"
    rttime = "rttime"
    sigpending = "sigpending"
    stack = "stack"


class Ulimit(BaseModel):
    name: UlimitResource = Field(..., description="The type of the ulimit.")
    soft_limit: int = Field(
        ..., alias="softLimit", description="The soft limit for the ulimit type."
    )
    hard_limit: int = Field(
        ..., alias="hardLimit", description="The hard limit for the ulimit type."
    )


class LogDriver(Enum):
    """
    The log driver to use for the container.  The valid values listed earlier are log
    drivers that the Amazon ECS container agent can communicate with by default.  For
    tasks using the Fargate launch type, the supported log drivers are awslogs, splunk,
    and awsfirelens.  For tasks using the EC2 launch type, the supported log drivers are
    awslogs, fluentd, gelf, json-file, journald, logentries,syslog, splunk, and
    awsfirelens.  For more information about using the awslogs log driver, see
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_awslogs.html Using
    the awslogs Log Driver in the Amazon Elastic Container Service Developer Guide.  For
    more information about using the awsfirelens log driver, see
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html
    Custom Log Routing in the Amazon Elastic Container Service Developer Guide.  If you
    have a custom driver that is not listed, you can fork the Amazon ECS container agent
    project that is https://github.com/aws/amazon-ecs-agent available on GitHub and
    customize it to work with that driver.  We encourage you to submit pull requests for
    changes that you would like to have included.  However, we do not currently provide
    support for running modified copies of this software.
    """

    json_file = "json-file"
    syslog = "syslog"
    journald = "journald"
    gelf = "gelf"
    fluentd = "fluentd"
    awslogs = "awslogs"
    splunk = "splunk"
    awsfirelens = "awsfirelens"


class SecretOption(BaseModel):
    name: str = Field(..., description="The name of the secret.")
    value_from: str = Field(
        ...,
        alias="valueFrom",
        description=(
            "The secret to expose to the container. The supported values are either the"
            " full ARN of the AWS Secrets Manager secret or the full ARN of the"
            " parameter in the AWS Systems Manager Parameter Store.  If the AWS Systems"
            " Manager Parameter Store parameter exists in the same Region as the task"
            " you are launching, then you can use either the full ARN or name of the"
            " parameter. If the parameter exists in a different Region, then the full"
            " ARN must be specified. "
        ),
    )


class EcsLogConfiguration(BaseModel):
    """
    The log configuration specification for the container.  This parameter maps to
    LogConfig in the https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate
    Create a container section of the https://docs.docker.com/engine/api/v1.35/ Docker
    Remote API and the --log-driver option to
    https://docs.docker.com/engine/reference/run/ docker run.  By default, containers
    use the same logging driver that the Docker daemon uses.  However the container may
    use a different logging driver than the Docker daemon by specifying a log driver
    with this parameter in the container definition.  To use a different logging driver
    for a container, the log system must be configured properly on the container
    instance (or on a different log server for remote logging options).  For more
    information on the options for different supported log drivers, see
    https://docs.docker.com/engine/admin/logging/overview/ Configure logging drivers in
    the Docker documentation.  Amazon ECS currently supports a subset of the logging
    drivers available to the Docker daemon (shown in the LogConfiguration data type).
    Additional log drivers may be available in future releases of the Amazon ECS
    container agent.  This parameter requires version 1.18 of the Docker Remote API or
    greater on your container instance.  To check the Docker Remote API version on your
    container instance, log in to your container instance and run the following command:
    sudo docker version --format '{{.Server.APIVersion}}' The Amazon ECS container agent
    running on a container instance must register the logging drivers available on that
    instance with the ECS_AVAILABLE_LOGGING_DRIVERS environment variable before
    containers placed on that instance can use these log configuration options.  For
    more information, see
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-config.html
    Amazon ECS Container Agent Configuration in the Amazon Elastic Container Service
    Developer Guide.
    """

    log_driver: LogDriver = Field(
        LogDriver.awslogs,
        alias="logDriver",
        description=(
            "The log driver to use for the container. The valid values listed earlier"
            " are log drivers that the Amazon ECS container agent can communicate with"
            " by default. For tasks using the Fargate launch type, the supported log"
            " drivers are awslogs, splunk, and awsfirelens. For tasks using the EC2"
            " launch type, the supported log drivers are awslogs, fluentd, gelf,"
            " json-file, journald, logentries,syslog, splunk, and awsfirelens. For more"
            " information about using the awslogs log driver, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_awslogs.html"  # noqa: E501
            " Using the awslogs Log Driver in the Amazon Elastic Container Service"
            " Developer Guide. For more information about using the awsfirelens log"
            " driver, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html"  # noqa: E501
            " Custom Log Routing in the Amazon Elastic Container Service Developer"
            " Guide.  If you have a custom driver that is not listed, you can fork the"
            " Amazon ECS container agent project that is"
            " https://github.com/aws/amazon-ecs-agent available on GitHub and customize"
            " it to work with that driver. We encourage you to submit pull requests for"
            " changes that you would like to have included. However, we do not"
            " currently provide support for running modified copies of this software. "
        ),
    )
    options: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "The configuration options to send to the log driver. This parameter"
            " requires version 1.19 of the Docker Remote API or greater on your"
            " container instance. To check the Docker Remote API version on your"
            " container instance, log in to your container instance and run the"
            " following command: sudo docker version --format '{{.Server.APIVersion}}' "
        ),
    )
    secret_options: Optional[List[SecretOption]] = Field(
        None,
        alias="secretOptions",
        description=(
            "The secrets to pass to the log configuration. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data.html"  # noqa: E501
            " Specifying Sensitive Data in the Amazon Elastic Container Service"
            " Developer Guide."
        ),
    )


class HealthCheck(BaseModel):
    """
    The container health check command and associated configuration parameters for the
    container.  This parameter maps to HealthCheck in the
    https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate Create a
    container section of the https://docs.docker.com/engine/api/v1.35/ Docker Remote API
    and the HEALTHCHECK parameter of https://docs.docker.com/engine/reference/run/
    docker run.
    """

    command: List[str] = Field(
        ...,
        description=(
            "A string array representing the command that the container runs to"
            " determine if it is healthy. The string array must start with CMD to"
            " execute the command arguments directly, or CMD-SHELL to run the command"
            ' with the container\'s default shell. For example:  [ "CMD-SHELL", "curl'
            ' -f http://localhost/ || exit 1" ]  An exit code of 0 indicates success,'
            " and non-zero exit code indicates failure. For more information, see"
            " HealthCheck in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API."
        ),
    )
    interval: Optional[int] = Field(
        None,
        description=(
            "The time period in seconds between each health check execution. You may"
            " specify between 5 and 300 seconds. The default value is 30 seconds."
        ),
    )
    timeout: Optional[int] = Field(
        None,
        description=(
            "The time period in seconds to wait for a health check to succeed before it"
            " is considered a failure. You may specify between 2 and 60 seconds. The"
            " default value is 5."
        ),
    )
    retries: Optional[int] = Field(
        None,
        description=(
            "The number of times to retry a failed health check before the container is"
            " considered unhealthy. You may specify between 1 and 10 retries. The"
            " default value is 3."
        ),
    )
    start_period: Optional[int] = Field(
        None,
        alias="startPeriod",
        description=(
            "The optional grace period within which to provide containers time to"
            " bootstrap before failed health checks count towards the maximum number of"
            " retries. You may specify between 0 and 300 seconds. The startPeriod is"
            " disabled by default.  If a health check succeeds within the startPeriod,"
            " then the container is considered healthy and any subsequent failures"
            " count toward the maximum number of retries. "
        ),
    )


class SystemControl(BaseModel):
    namespace: Optional[str] = Field(
        None, description="The namespaced kernel parameter for which to set a value."
    )
    parameter_value: Optional[str] = Field(
        None,
        alias="value",
        description=(
            "The value for the namespaced kernel parameter specified in namespace."
        ),
    )


class Type(Enum):
    """
    The type of resource to assign to a container.  The supported values are GPU or
    InferenceAccelerator.
    """

    gpu = "GPU"
    inference_accelerator = "InferenceAccelerator"


class ResourceRequirement(BaseModel):
    resource_value: str = Field(
        ...,
        alias="value",
        description=(
            "The value for the specified resource type. If the GPU type is used, the"
            " value is the number of physical GPUs the Amazon ECS container agent will"
            " reserve for the container. The number of GPUs reserved for all containers"
            " in a task should not exceed the number of available GPUs on the container"
            " instance the task is launched on. If the InferenceAccelerator type is"
            " used, the value should match the deviceName for an InferenceAccelerator"
            " specified in a task definition."
        ),
    )
    type: Type = Field(
        ...,
        description=(
            "The type of resource to assign to a container. The supported values are"
            " GPU or InferenceAccelerator."
        ),
    )


class FirelensLogRouters(Enum):
    """
    The log router to use. The valid values are fluentd or fluentbit.
    """

    fluentd = "fluentd"
    fluentbit = "fluentbit"


class FirelensConfiguration(BaseModel):
    """
    The FireLens configuration for the container.  This is used to specify and configure
    a log router for container logs.  For more information, see
    https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html
    Custom Log Routing in the Amazon Elastic Container Service Developer Guide.
    """

    type: FirelensLogRouters = Field(
        FirelensLogRouters.fluentbit,
        description="The log router to use. The valid values are fluentd or fluentbit.",
    )
    log_router_options: Optional[Dict[str, Union[str, bool]]] = Field(
        None,
        alias="options",
        description=(
            "The options to use when configuring the log router. This field is optional"
            " and can be used to specify a custom configuration file or to add"
            " additional metadata, such as the task, task definition, cluster, and"
            " container instance details to the log event. If specified, the syntax to"
            " use is"
            ' "options":{"enable-ecs-log-metadata":"true|false", '
            '"config-file-type:"s3|file", '
            '"config-file-value":"arn:aws:s3:::mybucket/fluent.conf|filepath"}.'
            " For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html#firelens-taskdef"  # noqa: E501
            " Creating a Task Definition that Uses a FireLens Configuration in the"
            " Amazon Elastic Container Service Developer Guide."
        ),
    )


class ContainerDefinition(BaseModel):
    name: Optional[str] = Field(
        None,
        description=(
            "The name of a container. If you are linking multiple containers together"
            " in a task definition, the name of one container can be entered in the"
            " links of another container to connect the containers. Up to 255 letters"
            " (uppercase and lowercase), numbers, and hyphens are allowed. This"
            " parameter maps to name in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --name option to https://docs.docker.com/engine/reference/run/ docker"
            " run. "
        ),
    )
    image: Optional[str] = Field(
        None,
        description=(
            "The image used to start a container. This string is passed directly to the"
            " Docker daemon. Images in the Docker Hub registry are available by"
            " default. Other repositories are specified with either "
            " repository-url/image:tag  or  repository-url/image@digest . Up to 255"
            " letters (uppercase and lowercase), numbers, hyphens, underscores, colons,"
            " periods, forward slashes, and number signs are allowed. This parameter"
            " maps to Image in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the IMAGE"
            " parameter of https://docs.docker.com/engine/reference/run/ docker run.  "
            " When a new task starts, the Amazon ECS container agent pulls the latest"
            " version of the specified image and tag for the container to use. However,"
            " subsequent updates to a repository image are not propagated to already"
            " running tasks.   Images in Amazon ECR repositories can be specified by"
            " either using the full registry/repository:tag or"
            " registry/repository@digest. For example,"
            " 012345678910.dkr.ecr.<region-name>.amazonaws.com/<repository-name>:latest"
            " or 012345678910.dkr.ecr.<region-name>.amazonaws.com/<repository-name>@sha256:94afd1f2e64d908bc90dbca0035a5b567EXAMPLE."  # noqa: E501
            "    Images in official repositories on Docker Hub use a single name (for"
            " example, ubuntu or mongo).   Images in other repositories on Docker Hub"
            " are qualified with an organization name (for example,"
            " amazon/amazon-ecs-agent).   Images in other online repositories are"
            " qualified further by a domain name (for example,"
            " quay.io/assemblyline/ubuntu).  "
        ),
    )
    repository_credentials: Optional[RepositoryCredentials] = Field(
        None,
        alias="repositoryCredentials",
        description="The private repository authentication credentials to use.",
    )
    cpu: Optional[int] = Field(
        None,
        description=(
            "The number of cpu units reserved for the container. This parameter maps to"
            " CpuShares in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --cpu-shares option to https://docs.docker.com/engine/reference/run/"
            " docker run. This field is optional for tasks using the Fargate launch"
            " type, and the only requirement is that the total amount of CPU reserved"
            " for all containers within a task be lower than the task-level cpu value. "
            " You can determine the number of CPU units that are available per EC2"
            " instance type by multiplying the vCPUs listed for that instance type on"
            " the http://aws.amazon.com/ec2/instance-types/ Amazon EC2 Instances detail"
            " page by 1,024.  Linux containers share unallocated CPU units with other"
            " containers on the container instance with the same ratio as their"
            " allocated amount. For example, if you run a single-container task on a"
            " single-core instance type with 512 CPU units specified for that"
            " container, and that is the only task running on the container instance,"
            " that container could use the full 1,024 CPU unit share at any given time."
            " However, if you launched another copy of the same task on that container"
            " instance, each task would be guaranteed a minimum of 512 CPU units when"
            " needed, and each container could float to higher CPU usage if the other"
            " container was not using it, but if both tasks were 100% active all of the"
            " time, they would be limited to 512 CPU units. On Linux container"
            " instances, the Docker daemon on the container instance uses the CPU value"
            " to calculate the relative CPU share ratios for running containers. For"
            " more information, see"
            " https://docs.docker.com/engine/reference/run/#cpu-share-constraint CPU"
            " share constraint in the Docker documentation. The minimum valid CPU share"
            " value that the Linux kernel allows is 2. However, the CPU parameter is"
            " not required, and you can use CPU values below 2 in your container"
            " definitions. For CPU values below 2 (including null), the behavior varies"
            " based on your Amazon ECS container agent version:    Agent versions less"
            " than or equal to 1.1.0: Null and zero CPU values are passed to Docker as"
            " 0, which Docker then converts to 1,024 CPU shares. CPU values of 1 are"
            " passed to Docker as 1, which the Linux kernel converts to two CPU shares."
            "    Agent versions greater than or equal to 1.2.0: Null, zero, and CPU"
            " values of 1 are passed to Docker as 2.   On Windows container instances,"
            " the CPU limit is enforced as an absolute limit, or a quota. Windows"
            " containers only have access to the specified amount of CPU that is"
            " described in the task definition."
        ),
    )
    memory: Optional[int] = Field(
        None,
        description=(
            "The amount (in MiB) of memory to present to the container. If your"
            " container attempts to exceed the memory specified here, the container is"
            " killed. The total amount of memory reserved for all containers within a"
            " task must be lower than the task memory value, if one is specified. This"
            " parameter maps to Memory in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --memory option to https://docs.docker.com/engine/reference/run/ docker"
            " run. If using the Fargate launch type, this parameter is optional. If"
            " using the EC2 launch type, you must specify either a task-level memory"
            " value or a container-level memory value. If you specify both a"
            " container-level memory and memoryReservation value, memory must be"
            " greater than memoryReservation. If you specify memoryReservation, then"
            " that value is subtracted from the available memory resources for the"
            " container instance on which the container is placed. Otherwise, the value"
            " of memory is used. The Docker daemon reserves a minimum of 4 MiB of"
            " memory for a container, so you should not specify fewer than 4 MiB of"
            " memory for your containers."
        ),
    )
    memory_reservation: Optional[int] = Field(
        None,
        alias="memoryReservation",
        description=(
            "The soft limit (in MiB) of memory to reserve for the container. When"
            " system memory is under heavy contention, Docker attempts to keep the"
            " container memory to this soft limit. However, your container can consume"
            " more memory when it needs to, up to either the hard limit specified with"
            " the memory parameter (if applicable), or all of the available memory on"
            " the container instance, whichever comes first. This parameter maps to"
            " MemoryReservation in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --memory-reservation option to"
            " https://docs.docker.com/engine/reference/run/ docker run. If a task-level"
            " memory value is not specified, you must specify a non-zero integer for"
            " one or both of memory or memoryReservation in a container definition. If"
            " you specify both, memory must be greater than memoryReservation. If you"
            " specify memoryReservation, then that value is subtracted from the"
            " available memory resources for the container instance on which the"
            " container is placed. Otherwise, the value of memory is used. For example,"
            " if your container normally uses 128 MiB of memory, but occasionally"
            " bursts to 256 MiB of memory for short periods of time, you can set a"
            " memoryReservation of 128 MiB, and a memory hard limit of 300 MiB. This"
            " configuration would allow the container to only reserve 128 MiB of memory"
            " from the remaining resources on the container instance, but also allow"
            " the container to consume more memory resources when needed. The Docker"
            " daemon reserves a minimum of 4 MiB of memory for a container, so you"
            " should not specify fewer than 4 MiB of memory for your containers. "
        ),
    )
    links: Optional[List[str]] = Field(
        None,
        description=(
            "The links parameter allows containers to communicate with each other"
            " without the need for port mappings. This parameter is only supported if"
            " the network mode of a task definition is bridge. The name:internalName"
            " construct is analogous to name:alias in Docker links. Up to 255 letters"
            " (uppercase and lowercase), numbers, and hyphens are allowed. For more"
            " information about linking Docker containers, go to"
            " https://docs.docker.com/network/links/ Legacy container links in the"
            " Docker documentation. This parameter maps to Links in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --link option to https://docs.docker.com/engine/reference/run/ docker"
            " run.  This parameter is not supported for Windows containers.  "
            " Containers that are collocated on a single container instance may be able"
            " to communicate with each other without requiring links or host port"
            " mappings. Network isolation is achieved on the container instance using"
            " security groups and VPC settings. "
        ),
    )
    port_mappings: Optional[List[PortMapping]] = Field(
        None,
        alias="portMappings",
        description=(
            "The list of port mappings for the container. Port mappings allow"
            " containers to access ports on the host container instance to send or"
            " receive traffic. For task definitions that use the awsvpc network mode,"
            " you should only specify the containerPort. The hostPort can be left blank"
            " or it must be the same value as the containerPort. Port mappings on"
            " Windows use the NetNAT gateway address rather than localhost. There is no"
            " loopback for port mappings on Windows, so you cannot access a container's"
            " mapped port from the host itself.  This parameter maps to PortBindings in"
            " the https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --publish option to https://docs.docker.com/engine/reference/run/ docker"
            " run. If the network mode of a task definition is set to none, then you"
            " can't specify port mappings. If the network mode of a task definition is"
            " set to host, then host ports must either be undefined or they must match"
            " the container port in the port mapping.  After a task reaches the RUNNING"
            " status, manual and automatic host and container port assignments are"
            " visible in the Network Bindings section of a container description for a"
            " selected task in the Amazon ECS console. The assignments are also visible"
            " in the networkBindings section DescribeTasks responses. "
        ),
    )
    essential: Optional[bool] = Field(
        None,
        description=(
            "If the essential parameter of a container is marked as true, and that"
            " container fails or stops for any reason, all other containers that are"
            " part of the task are stopped. If the essential parameter of a container"
            " is marked as false, then its failure does not affect the rest of the"
            " containers in a task. If this parameter is omitted, a container is"
            " assumed to be essential. All tasks must have at least one essential"
            " container. If you have an application that is composed of multiple"
            " containers, you should group containers that are used for a common"
            " purpose into components, and separate the different components into"
            " multiple task definitions. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/application_architecture.html"  # noqa: E501
            " Application Architecture in the Amazon Elastic Container Service"
            " Developer Guide."
        ),
    )
    entry_point: Optional[List[str]] = Field(
        None,
        alias="entryPoint",
        description=(
            " Early versions of the Amazon ECS container agent do not properly handle"
            " entryPoint parameters. If you have problems using entryPoint, update your"
            " container agent or enter your commands and arguments as command array"
            " items instead.  The entry point that is passed to the container. This"
            " parameter maps to Entrypoint in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --entrypoint option to https://docs.docker.com/engine/reference/run/"
            " docker run. For more information, see"
            " https://docs.docker.com/engine/reference/builder/#entrypoint"
            " https://docs.docker.com/engine/reference/builder/#entrypoint."
        ),
    )
    command: Optional[List[str]] = Field(
        None,
        description=(
            "The command that is passed to the container. This parameter maps to Cmd in"
            " the https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " COMMAND parameter to https://docs.docker.com/engine/reference/run/ docker"
            " run. For more information, see"
            " https://docs.docker.com/engine/reference/builder/#cmd"
            " https://docs.docker.com/engine/reference/builder/#cmd. If there are"
            " multiple arguments, each argument should be a separated string in the"
            " array."
        ),
    )
    environment: Optional[List[EnvironmentItem]] = Field(
        None,
        description=(
            "The environment variables to pass to a container. This parameter maps to"
            " Env in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the --env"
            " option to https://docs.docker.com/engine/reference/run/ docker run.  We"
            " do not recommend using plaintext environment variables for sensitive"
            " information, such as credential data. "
        ),
    )
    environment_files: Optional[List[EnvironmentFile]] = Field(
        None,
        alias="environmentFiles",
        description=(
            "A list of files containing the environment variables to pass to a"
            " container. This parameter maps to the --env-file option to"
            " https://docs.docker.com/engine/reference/run/ docker run. You can specify"
            " up to ten environment files. The file must have a .env file extension."
            " Each line in an environment file should contain an environment variable"
            " in VARIABLE=VALUE format. Lines beginning with # are treated as comments"
            " and are ignored. For more information on the environment variable file"
            " syntax, see https://docs.docker.com/compose/env-file/ Declare default"
            " environment variables in file. If there are environment variables"
            " specified using the environment parameter in a container definition, they"
            " take precedence over the variables contained within an environment file."
            " If multiple environment files are specified that contain the same"
            " variable, they are processed from the top down. It is recommended to use"
            " unique variable names. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/taskdef-envfiles.html"  # noqa: E501
            " Specifying Environment Variables in the Amazon Elastic Container Service"
            " Developer Guide. This field is not valid for containers in tasks using"
            " the Fargate launch type."
        ),
    )
    mount_points: Optional[List[MountPoint]] = Field(
        None,
        alias="mountPoints",
        description=(
            "The mount points for data volumes in your container. This parameter maps"
            " to Volumes in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --volume option to https://docs.docker.com/engine/reference/run/ docker"
            " run. Windows containers can mount whole directories on the same drive as"
            " $env:ProgramData. Windows containers cannot mount directories on a"
            " different drive, and mount point cannot be across drives."
        ),
    )
    volumes_from: Optional[List[VolumesFromItem]] = Field(
        None,
        alias="volumesFrom",
        description=(
            "Data volumes to mount from another container. This parameter maps to"
            " VolumesFrom in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --volumes-from option to https://docs.docker.com/engine/reference/run/"
            " docker run."
        ),
    )
    linux_parameters: Optional[LinuxParameters] = Field(
        None,
        alias="linuxParameters",
        description=(
            "Linux-specific modifications that are applied to the container, such as"
            " Linux kernel capabilities. For more information see KernelCapabilities. "
            " This parameter is not supported for Windows containers. "
        ),
    )
    secrets: Optional[List[AwsContainerSecret]] = Field(
        None,
        description=(
            "The secrets to pass to the container. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specifying-sensitive-data.html"  # noqa: E501
            " Specifying Sensitive Data in the Amazon Elastic Container Service"
            " Developer Guide."
        ),
    )
    depends_on: Optional[List[DependsOnItem]] = Field(
        None,
        alias="dependsOn",
        description=(
            "The dependencies defined for container startup and shutdown. A container"
            " can contain multiple dependencies. When a dependency is defined for"
            " container startup, for container shutdown it is reversed. For tasks using"
            " the EC2 launch type, the container instances require at least version"
            " 1.26.0 of the container agent to enable container dependencies. However,"
            " we recommend using the latest container agent version. For information"
            " about checking your agent version and updating to the latest version, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-update.html"  # noqa: E501
            " Updating the Amazon ECS Container Agent in the Amazon Elastic Container"
            " Service Developer Guide. If you are using an Amazon ECS-optimized Linux"
            " AMI, your instance needs at least version 1.26.0-1 of the ecs-init"
            " package. If your container instances are launched from version 20190301"
            " or later, then they contain the required versions of the container agent"
            " and ecs-init. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html"  # noqa: E501
            " Amazon ECS-optimized Linux AMI in the Amazon Elastic Container Service"
            " Developer Guide. For tasks using the Fargate launch type, the task or"
            " service requires platform version 1.3.0 or later."
        ),
    )
    start_timeout: Optional[int] = Field(
        None,
        alias="startTimeout",
        description=(
            "Time duration (in seconds) to wait before giving up on resolving"
            " dependencies for a container. For example, you specify two containers in"
            " a task definition with containerA having a dependency on containerB"
            " reaching a COMPLETE, SUCCESS, or HEALTHY status. If a startTimeout value"
            " is specified for containerB and it does not reach the desired status"
            " within that time then containerA will give up and not start. This results"
            " in the task transitioning to a STOPPED state. For tasks using the Fargate"
            " launch type, this parameter requires that the task or service uses"
            " platform version 1.3.0 or later. If this parameter is not specified, the"
            " default value of 3 minutes is used. For tasks using the EC2 launch type,"
            " if the startTimeout parameter is not specified, the value set for the"
            " Amazon ECS container agent configuration variable"
            " ECS_CONTAINER_START_TIMEOUT is used by default. If neither the"
            " startTimeout parameter or the ECS_CONTAINER_START_TIMEOUT agent"
            " configuration variable are set, then the default values of 3 minutes for"
            " Linux containers and 8 minutes on Windows containers are used. Your"
            " container instances require at least version 1.26.0 of the container"
            " agent to enable a container start timeout value. However, we recommend"
            " using the latest container agent version. For information about checking"
            " your agent version and updating to the latest version, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-update.html"  # noqa: E501
            " Updating the Amazon ECS Container Agent in the Amazon Elastic Container"
            " Service Developer Guide. If you are using an Amazon ECS-optimized Linux"
            " AMI, your instance needs at least version 1.26.0-1 of the ecs-init"
            " package. If your container instances are launched from version 20190301"
            " or later, then they contain the required versions of the container agent"
            " and ecs-init. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html"  # noqa: E501
            " Amazon ECS-optimized Linux AMI in the Amazon Elastic Container Service"
            " Developer Guide."
        ),
    )
    stop_timeout: Optional[int] = Field(
        None,
        alias="stopTimeout",
        description=(
            "Time duration (in seconds) to wait before the container is forcefully"
            " killed if it doesn't exit normally on its own. For tasks using the"
            " Fargate launch type, the task or service requires platform version 1.3.0"
            " or later. The max stop timeout value is 120 seconds and if the parameter"
            " is not specified, the default value of 30 seconds is used. For tasks"
            " using the EC2 launch type, if the stopTimeout parameter is not specified,"
            " the value set for the Amazon ECS container agent configuration variable"
            " ECS_CONTAINER_STOP_TIMEOUT is used by default. If neither the stopTimeout"
            " parameter or the ECS_CONTAINER_STOP_TIMEOUT agent configuration variable"
            " are set, then the default values of 30 seconds for Linux containers and"
            " 30 seconds on Windows containers are used. Your container instances"
            " require at least version 1.26.0 of the container agent to enable a"
            " container stop timeout value. However, we recommend using the latest"
            " container agent version. For information about checking your agent"
            " version and updating to the latest version, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-update.html"  # noqa: E501
            " Updating the Amazon ECS Container Agent in the Amazon Elastic Container"
            " Service Developer Guide. If you are using an Amazon ECS-optimized Linux"
            " AMI, your instance needs at least version 1.26.0-1 of the ecs-init"
            " package. If your container instances are launched from version 20190301"
            " or later, then they contain the required versions of the container agent"
            " and ecs-init. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html"  # noqa: E501
            " Amazon ECS-optimized Linux AMI in the Amazon Elastic Container Service"
            " Developer Guide."
        ),
    )
    hostname: Optional[str] = Field(
        None,
        description=(
            "The hostname to use for your container. This parameter maps to Hostname in"
            " the https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --hostname option to https://docs.docker.com/engine/reference/run/ docker"
            " run.  The hostname parameter is not supported if you are using the awsvpc"
            " network mode. "
        ),
    )
    user: Optional[str] = Field(
        None,
        description=(
            "The user name to use inside the container. This parameter maps to User in"
            " the https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --user option to https://docs.docker.com/engine/reference/run/ docker"
            " run. You can use the following formats. If specifying a UID or GID, you"
            " must specify it as a positive integer.    user     user:group     uid    "
            " uid:gid     user:gid     uid:group     This parameter is not supported"
            " for Windows containers. "
        ),
    )
    working_directory: Optional[str] = Field(
        None,
        alias="workingDirectory",
        description=(
            "The working directory in which to run commands inside the container. This"
            " parameter maps to WorkingDir in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --workdir option to https://docs.docker.com/engine/reference/run/ docker"
            " run."
        ),
    )
    disable_networking: Optional[bool] = Field(
        None,
        alias="disableNetworking",
        description=(
            "When this parameter is true, networking is disabled within the container."
            " This parameter maps to NetworkDisabled in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API.  This"
            " parameter is not supported for Windows containers. "
        ),
    )
    privileged: Optional[bool] = Field(
        None,
        description=(
            "When this parameter is true, the container is given elevated privileges on"
            " the host container instance (similar to the root user). This parameter"
            " maps to Privileged in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --privileged option to https://docs.docker.com/engine/reference/run/"
            " docker run.  This parameter is not supported for Windows containers or"
            " tasks using the Fargate launch type. "
        ),
    )
    readonly_root_filesystem: Optional[bool] = Field(
        None,
        alias="readonlyRootFilesystem",
        description=(
            "When this parameter is true, the container is given read-only access to"
            " its root file system. This parameter maps to ReadonlyRootfs in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --read-only option to https://docs.docker.com/engine/reference/run/"
            " docker run.  This parameter is not supported for Windows containers. "
        ),
    )
    dns_servers: Optional[List[str]] = Field(
        None,
        alias="dnsServers",
        description=(
            "A list of DNS servers that are presented to the container. This parameter"
            " maps to Dns in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the --dns"
            " option to https://docs.docker.com/engine/reference/run/ docker run.  This"
            " parameter is not supported for Windows containers. "
        ),
    )
    dns_search_domains: Optional[List[str]] = Field(
        None,
        alias="dnsSearchDomains",
        description=(
            "A list of DNS search domains that are presented to the container. This"
            " parameter maps to DnsSearch in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --dns-search option to https://docs.docker.com/engine/reference/run/"
            " docker run.  This parameter is not supported for Windows containers. "
        ),
    )
    extra_hosts: Optional[List[ExtraHost]] = Field(
        None,
        alias="extraHosts",
        description=(
            "A list of hostnames and IP address mappings to append to the /etc/hosts"
            " file on the container. This parameter maps to ExtraHosts in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --add-host option to https://docs.docker.com/engine/reference/run/ docker"
            " run.  This parameter is not supported for Windows containers or tasks"
            " that use the awsvpc network mode. "
        ),
    )
    docker_security_options: Optional[List[str]] = Field(
        None,
        alias="dockerSecurityOptions",
        description=(
            "A list of strings to provide custom labels for SELinux and AppArmor"
            " multi-level security systems. This field is not valid for containers in"
            " tasks using the Fargate launch type. With Windows containers, this"
            " parameter can be used to reference a credential spec file when"
            " configuring a container for Active Directory authentication. For more"
            " information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/windows-gmsa.html"  # noqa: E501
            " Using gMSAs for Windows Containers in the Amazon Elastic Container"
            " Service Developer Guide. This parameter maps to SecurityOpt in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --security-opt option to https://docs.docker.com/engine/reference/run/"
            " docker run.  The Amazon ECS container agent running on a container"
            " instance must register with the ECS_SELINUX_CAPABLE=true or"
            " ECS_APPARMOR_CAPABLE=true environment variables before containers placed"
            " on that instance can use these security options. For more information,"
            " see https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-config.html"  # noqa: E501
            " Amazon ECS Container Agent Configuration in the Amazon Elastic Container"
            " Service Developer Guide. "
        ),
    )
    interactive: Optional[bool] = Field(
        None,
        description=(
            "When this parameter is true, this allows you to deploy containerized"
            " applications that require stdin or a tty to be allocated. This parameter"
            " maps to OpenStdin in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --interactive option to https://docs.docker.com/engine/reference/run/"
            " docker run."
        ),
    )
    pseudo_terminal: Optional[bool] = Field(
        None,
        alias="pseudoTerminal",
        description=(
            "When this parameter is true, a TTY is allocated. This parameter maps to"
            " Tty in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the --tty"
            " option to https://docs.docker.com/engine/reference/run/ docker run."
        ),
    )
    docker_labels: Optional[Dict[str, str]] = Field(
        None,
        alias="dockerLabels",
        description=(
            "A key/value map of labels to add to the container. This parameter maps to"
            " Labels in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --label option to https://docs.docker.com/engine/reference/run/ docker"
            " run. This parameter requires version 1.18 of the Docker Remote API or"
            " greater on your container instance. To check the Docker Remote API"
            " version on your container instance, log in to your container instance and"
            " run the following command: sudo docker version --format"
            " '{{.Server.APIVersion}}' "
        ),
    )
    ulimits: Optional[List[Ulimit]] = Field(
        None,
        description=(
            "A list of ulimits to set in the container. If a ulimit value is specified"
            " in a task definition, it will override the default values set by Docker."
            " This parameter maps to Ulimits in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --ulimit option to https://docs.docker.com/engine/reference/run/ docker"
            " run. Valid naming values are displayed in the Ulimit data type. This"
            " parameter requires version 1.18 of the Docker Remote API or greater on"
            " your container instance. To check the Docker Remote API version on your"
            " container instance, log in to your container instance and run the"
            " following command: sudo docker version --format '{{.Server.APIVersion}}' "
            "  This parameter is not supported for Windows containers. "
        ),
    )
    log_configuration: Optional[EcsLogConfiguration] = Field(
        None,
        alias="logConfiguration",
        description=(
            "The log configuration specification for the container. This parameter maps"
            " to LogConfig in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --log-driver option to https://docs.docker.com/engine/reference/run/"
            " docker run. By default, containers use the same logging driver that the"
            " Docker daemon uses. However the container may use a different logging"
            " driver than the Docker daemon by specifying a log driver with this"
            " parameter in the container definition. To use a different logging driver"
            " for a container, the log system must be configured properly on the"
            " container instance (or on a different log server for remote logging"
            " options). For more information on the options for different supported log"
            " drivers, see https://docs.docker.com/engine/admin/logging/overview/"
            " Configure logging drivers in the Docker documentation.  Amazon ECS"
            " currently supports a subset of the logging drivers available to the"
            " Docker daemon (shown in the LogConfiguration data type). Additional log"
            " drivers may be available in future releases of the Amazon ECS container"
            " agent.  This parameter requires version 1.18 of the Docker Remote API or"
            " greater on your container instance. To check the Docker Remote API"
            " version on your container instance, log in to your container instance and"
            " run the following command: sudo docker version --format"
            " '{{.Server.APIVersion}}'   The Amazon ECS container agent running on a"
            " container instance must register the logging drivers available on that"
            " instance with the ECS_AVAILABLE_LOGGING_DRIVERS environment variable"
            " before containers placed on that instance can use these log configuration"
            " options. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-config.html"  # noqa: E501
            " Amazon ECS Container Agent Configuration in the Amazon Elastic Container"
            " Service Developer Guide. "
        ),
    )
    health_check: Optional[HealthCheck] = Field(
        None,
        alias="healthCheck",
        description=(
            "The container health check command and associated configuration parameters"
            " for the container. This parameter maps to HealthCheck in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " HEALTHCHECK parameter of https://docs.docker.com/engine/reference/run/"
            " docker run."
        ),
    )
    system_controls: Optional[List[SystemControl]] = Field(
        None,
        alias="systemControls",
        description=(
            "A list of namespaced kernel parameters to set in the container. This"
            " parameter maps to Sysctls in the"
            " https://docs.docker.com/engine/api/v1.35/#operation/ContainerCreate"
            " Create a container section of the"
            " https://docs.docker.com/engine/api/v1.35/ Docker Remote API and the"
            " --sysctl option to https://docs.docker.com/engine/reference/run/ docker"
            " run.  It is not recommended that you specify network-related"
            " systemControls parameters for multiple containers in a single task that"
            " also uses either the awsvpc or host network modes. For tasks that use the"
            " awsvpc network mode, the container that is started last determines which"
            " systemControls parameters take effect. For tasks that use the host"
            " network mode, it changes the container instance's namespaced kernel"
            " parameters as well as the containers. "
        ),
    )
    resource_requirements: Optional[List[ResourceRequirement]] = Field(
        None,
        alias="resourceRequirements",
        description=(
            "The type and amount of a resource to assign to a container. The only"
            " supported resource is a GPU."
        ),
    )
    firelens_configuration: Optional[FirelensConfiguration] = Field(
        None,
        alias="firelensConfiguration",
        description=(
            "The FireLens configuration for the container. This is used to specify and"
            " configure a log router for container logs. For more information, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html"  # noqa: E501
            " Custom Log Routing in the Amazon Elastic Container Service Developer"
            " Guide."
        ),
    )
