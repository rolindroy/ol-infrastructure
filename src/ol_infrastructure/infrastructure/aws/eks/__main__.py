import pulumi
import pulumi_aws as aws

from bridge.lib.magic_numbers import DEFAULT_HTTPS_PORT
from ol_infrastructure.lib.aws.ec2_helper import default_egress_args
from ol_infrastructure.lib.aws.iam_helper import lint_iam_policy
from ol_infrastructure.lib.ol_types import AWSBase
from ol_infrastructure.lib.pulumi_helper import parse_stack

SEARCH_DOMAIN_NAME_MAX_LENGTH = 28

###############
# STACK SETUP #
###############
eks_config = pulumi.Config("eks")
env_config = pulumi.Config("environment")
stack_info = parse_stack()
network_stack = pulumi.StackReference(f"infrastructure.aws.network.{stack_info.name}")
# TODO:
# consul_stack = pulumi.StackReference(
#    f"infrastructure.consul.{stack_info.env_prefix}.{stack_info.name}"
# )
# vault_stack = pulumi.StackReference(
#    f"infrastructure.vault.operations.{stack_info.name}"
# )

#############
# VARIABLES #
#############
environment_name = f"{stack_info.env_prefix}-{stack_info.env_suffix}"
target_vpc = network_stack.require_output(env_config.require("target_vpc"))
business_unit = env_config.get("business_unit") or "operations"
aws_config = AWSBase(tags={"OU": business_unit, "Environment": environment_name})
# TODO:
# consul_service_name = (
#    search_config.get("consul_service_name") or "elasticsearch"
# )  # Default is for legacy compatability

##########
# CREATE #
##########

# Networking
network_config = eks_config.get("networking")

# Firstly block off the Service address space.
# We will never create explicit AWS resources here but we want to protect it from
# other actors and overlapping the address space which would be bad.

sg_ingress_rules = [
    aws.ec2.SecurityGroupIngressArgs(
        from_port=DEFAULT_HTTPS_PORT,
        to_port=DEFAULT_HTTPS_PORT,
        cidr_blocks=["0.0.0.0/0"],
        protocol="tcp",
    )
]
sg_egress_rules = [
    aws.ec2.SecurityGroupEgressArgs(
        cidr_blocks=["0.0.0.0/0"],
        from_port=0,
        protocol="-1",
        to_port=0,
    )
]
search_security_group = aws.ec2.SecurityGroup(
    "opensearch-security-group",
    name_prefix=f"{environment_name}-opensearch-",
    tags=aws_config.merged_tags({"Name": f"{environment_name}-opensearch"}),
    description="Grant access to the OpenSearch service domain",
    egress=default_egress_args,
    ingress=sg_ingress_rules,
    vpc_id=target_vpc["id"],
)

# IAM Resources
policy_path = "/ol-operations/eks-{environment_name}/"
cloudwatch_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {"Action": ["cloudwatch:PutMetricData"], "Resource": "*", "Effect": "Allow"}
    ],
}
cloudwatch_policy = aws.iam.Policy(
    "aws-eks-cloudwatch-policy",
    name=f"eksctl-{environment_name}-cluster-PolicyCloudWatchMetrics",
    path=policy_path,
    policy=lint_iam_policy(cloudwatch_policy_document, stringify=True),
    description="Policy permitting the the cluster to ship metrics to cloudwatch.",
)
elb_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:DescribeAccountAttributes",
                "ec2:DescribeAddresses",
                "ec2:DescribeInternetGateways",
            ],
            "Resource": "*",
            "Effect": "Allow",
        }
    ],
}
elb_policy = aws.iam.Policy(
    "aws-eks-elb-policy",
    name=f"eksctl-{environment_name}-cluster-PolicyELBPermissions",
    path=policy_path,
    policy=lint_iam_policy(elb_policy_document, stringify=True),
    description="Policy permitting the cluster to interact with ELB resources.",
)
cluster_role = aws.iam.Role(
    "aws-eks-cluster-role",
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
""",
)


aws.iam.RolePolicyAttachment(
    "cluster_role-AmazonEKSClusterPolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    role=cluster_role.name,
)
aws.iam.RolePolicyAttachment(
    "cluster_role-AmazonEKSVPCResourceController",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSVPCResourceController",
    role=cluster_role.name,
)
aws.iam.RolePolicyAttachment(
    "CloudWatchPolicy",
    policy_arn=cloudwatch_policy.arn,
    role=cluster_role.name,
)
aws.iam.RolePolicyAttachment(
    "ELBPolicy",
    policy_arn=elb_policy.arn,
    role=cluster_role.name,
)

# Misc EKS configuration Items
# Logging Configuration
logging_config = eks_config.get_object("logging")
log_types = logging_config["log_types"]

# Encryption Configuration
# TODO

# Network Configuration
cluster_network_config = aws.eks.ClusterKubernetesNetworkConfigArgs(
    ip_family="ipv4", service_ipv4_cidr=target_vpc["k8s_service_subnet"]
)
# cluster_vpc_config = aws.eks.ClusterVpcConfigArgs(subnet_ids=target_vpc["subnet_ids"], vpc_id=target_vpc["id"])
cluster_vpc_config = aws.eks.ClusterVpcConfigArgs(subnet_ids=target_vpc["subnet_ids"])

# EKS Cluster
cluster = aws.eks.Cluster(
    f"awseks-{environment_name}-cluster",
    enabled_cluster_log_types=log_types,
    #          encryption_config=cluster_encryption_config or None,
    kubernetes_network_config=cluster_network_config or None,
    name=f"awseks-{environment_name}-cluster",
    role_arn=cluster_role.arn,
    tags=aws_config.merged_tags({"Name": f"awseks-{environment_name}-cluster"}),
    version=eks_config.get("version") or None,
    vpc_config=cluster_vpc_config or None,
)
