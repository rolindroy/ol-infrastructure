import json

from pulumi import Config, ResourceOptions, StackReference, export
from pulumi_aws import autoscaling, ec2, get_caller_identity, iam, route53

from bridge.lib.magic_numbers import (
    CONSUL_DNS_PORT,
    CONSUL_HTTP_PORT,
    CONSUL_LAN_SERF_PORT,
    CONSUL_RPC_PORT,
    CONSUL_WAN_SERF_PORT,
)
from ol_infrastructure.lib.aws.ec2_helper import (
    DiskTypes,
    InstanceTypes,
    availability_zones,
    debian_10_ami,
    default_egress_args,
)
from ol_infrastructure.lib.consul import build_consul_userdata
from ol_infrastructure.lib.ol_types import AWSBase
from ol_infrastructure.lib.pulumi_helper import parse_stack

stack_info = parse_stack()
env_config = Config("environment")
consul_config = Config("consul")
environment_name = f"{stack_info.env_prefix}-{stack_info.env_suffix}"
business_unit = env_config.get("business_unit") or "operations"
network_stack = StackReference(f"infrastructure.aws.network.{stack_info.name}")
policy_stack = StackReference("infrastructure.aws.policies")
destination_vpc = network_stack.require_output(env_config.require("vpc_reference"))
peer_vpcs = destination_vpc["peers"].apply(
    lambda peers: {peer: network_stack.require_output(peer) for peer in peers}
)
aws_config = AWSBase(tags={"OU": business_unit, "Environment": environment_name})
destination_vpc = network_stack.require_output(env_config.require("vpc_reference"))
dns_stack = StackReference("infrastructure.aws.dns")
mitodl_zone_id = dns_stack.require_output("odl_zone_id")


#############
# IAM Setup #
#############

consul_instance_role = iam.Role(
    f"consul-instance-role-{environment_name}",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Action": "sts:AssumeRole",
                "Principal": {"Service": "ec2.amazonaws.com"},
            },
        }
    ),
    path="/ol-operations/consul/role/",
    tags=aws_config.tags,
)

iam.RolePolicyAttachment(
    f"consul-describe-instance-role-policy-{environment_name}",
    policy_arn=policy_stack.require_output("iam_policies")["describe_instances"],
    role=consul_instance_role.name,
)

consul_instance_profile = iam.InstanceProfile(
    f"consul-instance-profile-{environment_name}",
    role=consul_instance_role.name,
    path="/ol-operations/consul/profile/",
)


########################
# Security Group Setup #
########################

consul_server_security_group = ec2.SecurityGroup(
    f"consul-server-{environment_name}-security-group",
    name=f"{environment_name}-consul-server",
    description="Access control between Consul severs and agents",
    tags=aws_config.merged_tags({"Name": f"{environment_name}-consul-server"}),
    vpc_id=destination_vpc["id"],
    ingress=[
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=[destination_vpc["cidr"]],
            protocol="tcp",
            from_port=CONSUL_HTTP_PORT,
            to_port=CONSUL_HTTP_PORT,
            description="HTTP API access",
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=[destination_vpc["cidr"]],
            protocol="udp",
            from_port=CONSUL_HTTP_PORT,
            to_port=CONSUL_HTTP_PORT,
            description="HTTP API access",
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=[destination_vpc["cidr"]],
            protocol="tcp",
            from_port=CONSUL_DNS_PORT,
            to_port=CONSUL_DNS_PORT,
            description="DNS access",
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=[destination_vpc["cidr"]],
            protocol="udp",
            from_port=CONSUL_DNS_PORT,
            to_port=CONSUL_DNS_PORT,
            description="DNS access",
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=[destination_vpc["cidr"]],
            protocol="tcp",
            from_port=CONSUL_RPC_PORT,
            to_port=CONSUL_LAN_SERF_PORT,
            description="LAN gossip protocol",
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=[destination_vpc["cidr"]],
            protocol="udp",
            from_port=CONSUL_RPC_PORT,
            to_port=CONSUL_LAN_SERF_PORT,
            description="LAN gossip protocol",
        ),
        ec2.SecurityGroupIngressArgs(
            cidr_blocks=peer_vpcs.apply(
                lambda peer_vpcs: [peer["cidr"] for peer in peer_vpcs.values()]
            ),
            protocol="tcp",
            from_port=CONSUL_RPC_PORT,
            to_port=CONSUL_WAN_SERF_PORT,
            description="WAN cross-datacenter communication",
        ),
    ],
    egress=default_egress_args,
)

consul_agent_security_group = ec2.SecurityGroup(
    f"consul-agent-{environment_name}-security-group",
    name=f"{environment_name}-consul-agent",
    description="Access control between Consul agents",
    tags=aws_config.merged_tags({"Name": f"{environment_name}-consul-agent"}),
    vpc_id=destination_vpc["id"],
    ingress=[
        ec2.SecurityGroupIngressArgs(
            security_groups=[consul_server_security_group.id],
            protocol="tcp",
            from_port=CONSUL_LAN_SERF_PORT,
            to_port=CONSUL_LAN_SERF_PORT,
            self=True,
            description="LAN gossip protocol from servers",
        ),
        ec2.SecurityGroupIngressArgs(
            security_groups=[consul_server_security_group.id],
            protocol="udp",
            from_port=CONSUL_LAN_SERF_PORT,
            to_port=CONSUL_LAN_SERF_PORT,
            self=True,
            description="LAN gossip protocol from servers",
        ),
    ],
)

security_groups = {
    "consul_server": consul_server_security_group.id,
    "consul_agent": consul_agent_security_group.id,
}


##################
# Route 53 Setup #
##################

fifteen_minutes = 60 * 15
# TODO set up to reference LB
consul_domain = route53.Record(
    f"consul-{environment_name}-dns-record",
    # name=f"consul-{salt_environment}.odl.mit.edu",
    type="A",
    ttl=fifteen_minutes,
    records=[consul_server.public_ip for consul_server in consul_instances],
    zone_id=mitodl_zone_id,
    opts=ResourceOptions(depends_on=consul_instances),
)


#########################
# Launch Template Setup #
#########################

# Find AMI
aws_account = get_caller_identity()
consul_ami = ec2.get_ami(
    filters=[
        ec2.GetAmiFilterArgs(name="name", values=["consul"]),
        ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
        ec2.GetAmiFilterArgs(name="root-device-type", values=["ebs"]),
    ],
    most_recent=True,
    owners=[aws_account.account_id],
)

# Select instance type
instance_type_name = consul_config.get("instance_type") or InstanceTypes.medium.name
instance_type = InstanceTypes[instance_type_name].value

consul_launch_config = ec2.LaunchTemplate(
    "consul-launch-template",
    name_prefix=f"consul-{environment_name}-",
    description="Launch template for deploying Consul cluster",
    # block_device_mappings  TODO: additional block device mappings needed here, or to be defined in AMI?
    iam_instance_profile=consul_instance_profile.id,
    image_id=consul_ami.id,
    instance_type=instance_type,
    key_name="oldevops",
    tags=aws_config.tags,
    # TODO: tag volumes via LaunchTemplate, or in AMI?
    tag_specifications=[
        ec2.LaunchTemplateTagSpecificationArgs(
            resource_type="instance",
            tags=aws_config.merged_tags({"Name": f"consul-{stack_info.env_suffix}"}),
        ),
        ec2.LaunchTemplateTagSpecificationArgs(
            resource_type="volume",
            tags=aws_config.merged_tags({"Name": f"consul-{stack_info.env_suffix}"}),
        ),
    ],
    user_data=build_consul_userdata(
        env_name=environment_name,
    ),
    vpc_security_group_ids=[
        destination_vpc["security_groups"]["web"],
        security_groups["consul_server"],
        security_groups["consul_agent"],
    ],
)


#########################
# Autoscale Group Setup #
#########################


# instance_count should be 1, 3, or 5
consul_capacity = consul_config.get_int("instance_count") or 3

# Define list of available subnets -- vpc zone identifiers -- for autoscale group
subnet_ids = destination_vpc["subnet_ids"]

consul_asg = autoscaling.Group(
    f"consul-{environment_name}-autoscaling-group",
    availability_zones=availability_zones,
    desired_capacity=consul_capacity,
    max_size=consul_capacity,
    min_size=consul_capacity,
    health_check_type="EC2",  # consider custom health check to verify consul health
    launch_template=autoscaling.GroupLaunchTemplateArgs(
        id=consul_launch_config.id,
        version="$Latest",
    ),
    instance_type_name=None,
    instance_refresh=autoscaling.GroupInstanceRefreshArgs(
            strategy="Rolling",
    ),
    tags=[
        autoscaling.GroupTagArgs(
            key=key_name,
            value=key_value,
            propagate_at_launch=True,
        )
        for key_name, key_value in aws_config.tags.items()
    ],
    vpc_zone_identifiers=subnet_ids,
)


#################
# Stack Exports #
#################

export("security_groups", security_groups)
export("instances", export_data)  # TODO: export LB reference
export("consul_launch_config", consul_launch_config.id)
export("consul_asg", consul_asg.id)
