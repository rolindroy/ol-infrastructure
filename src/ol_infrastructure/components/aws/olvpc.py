# coding: utf-8
"""This module defines a Pulumi component resource for encapsulating our best practices for building an AWS VPC.

This includes:

- Create the named VPC with appropriate tags
- Create a minimum of 3 subnets across multiple availability zones
- Create an internet gateway
- Create an IPv6 egress gateway
- Create a route table and associate the created subnets with it
- Create a routing table to include the relevant peers and their networks
- Create an RDS subnet group
"""
from ipaddress import IPv4Network, IPv6Network
from itertools import cycle
from typing import List, Optional, Text

from pulumi import ComponentResource, ResourceOptions
from pulumi_aws import ec2, rds
from pydantic import PositiveInt, validator

from ol_infrastructure.lib.aws.ec2_helper import (
    availability_zones,
    internet_gateway_opts,
    route_table_opts,
    subnet_opts,
    vpc_opts
)
from ol_infrastructure.lib.ol_types import AWSBase

MIN_SUBNETS = PositiveInt(3)
MAX_NET_PREFIX = 21  # A CIDR block of prefix length 21 allows for up to 8 /24 subnet blocks
SUBNET_PREFIX_V4 = 24  # A CIDR block of prefix length 24 allows for up to 255 individual IP addresses
SUBNET_PREFIX_V6 = 64


class OLVPCConfig(AWSBase):
    """Schema definition for VPC configuration values."""
    vpc_name: Text
    cidr_block: IPv4Network
    num_subnets: PositiveInt = MIN_SUBNETS
    enable_ipv6: bool = True
    default_public_ip: bool = True

    @validator('cidr_block')
    def is_private_net(cls: 'OLVPCConfig', network: IPv4Network) -> IPv4Network:  # noqa: N805
        """Ensure that only private subnets are assigned to VPC.

        :param cls: Class object of OLVPCConfig
        :type cls: OLVPCConfig

        :param network: CIDR block configured for the VPC to be created
        :type network: IPv4Network

        :raises ValueError: Raise a ValueError if the CIDR block is not for an RFC1918 private network, or is too small

        :returns: IPv4Network object passed to validator function

        :rtype: IPv4Network
        """
        if not network.is_private:
            raise ValueError('Specified CIDR block for VPC is not an RFC1918 private network')
        if network.prefixlen > MAX_NET_PREFIX:
            raise ValueError(
                'Specified CIDR block has a prefix that is too large. '
                'Please specify a network with a prefix length between /16 and /21')
        return network

    @validator('num_subnets')
    def min_subnets(cls: 'OLVPCConfig', num_nets: PositiveInt) -> PositiveInt:  # noqa: N805
        """Enforce that no fewer than the minimum number of subnets are created.

        :param cls: Class object of OLVPCConfig
        :type cls: OLVPCConfig

        :param num_nets: Number of subnets to be created in the VPC
        :type num_nets: PositiveInt

        :raises ValueError: Raise a ValueError if the number of subnets is fewer than MIN_SUBNETS

        :returns: The number of subnets to be created in the VPC

        :rtype: PositiveInt
        """
        if num_nets < MIN_SUBNETS:
            raise ValueError(
                'There should be at least 2 subnets defined for a VPC to allow for high availability '
                'across availability zones')
        return num_nets


class OLVPC(ComponentResource):
    """Pulumi component for building all of the necessary pieces of an AWS VPC.

    A component resource that encapsulates all of the standard practices of how the Open Learning Platform Engineering
    team constructs and organizes VPC environments in AWS.
    """
    def __init__(self, vpc_config: OLVPCConfig, opts: Optional[ResourceOptions] = None):  # noqa: WPS210
        """Build an AWS VPC with subnets, internet gateway, and routing table.

        :param vpc_config: Configuration object for customizing the created VPC and associated resources.
        :type vpc_config: OLVPCConfig
        """
        super().__init__('ol:infrastructure:aws:VPC', vpc_config.vpc_name, None, opts)
        resource_options = ResourceOptions.merge(ResourceOptions(parent=self), opts)  # type: ignore
        self.vpc_config = vpc_config
        vpc_resource_opts, imported_vpc_id = vpc_opts(vpc_config.cidr_block)
        self.olvpc = ec2.Vpc(
            vpc_config.vpc_name,
            cidr_block=str(vpc_config.cidr_block),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            assign_generated_ipv6_cidr_block=vpc_config.enable_ipv6,
            tags=vpc_config.tags,
            opts=ResourceOptions.merge(resource_options, vpc_resource_opts)
        )

        internet_gateway_resource_opts, imported_gateway_id = internet_gateway_opts(imported_vpc_id)
        self.gateway = ec2.InternetGateway(
            f'{vpc_config.vpc_name}-internet-gateway',
            vpc_id=self.olvpc.id,
            tags=vpc_config.tags,
            opts=ResourceOptions.merge(resource_options, internet_gateway_resource_opts)
        )

        self.egress_gateway = ec2.EgressOnlyInternetGateway(
            f'{vpc_config.vpc_name}-egress-internet-gateway',
            opts=resource_options,
            vpc_id=self.olvpc.id,
            tags=vpc_config.tags
        )

        route_table_resource_opts, imported_route_table_id = route_table_opts(imported_gateway_id)
        self.route_table = ec2.RouteTable(
            f'{vpc_config.vpc_name}-route-table',
            tags=vpc_config.tags,
            vpc_id=self.olvpc.id,
            routes=[
                {
                    'cidr_block': '0.0.0.0/0',
                    'gateway_id': self.gateway.id
                },
                {
                    'ipv6CidrBlock': '::/0',
                    'egressOnlyGatewayId': self.egress_gateway.id
                }
            ],
            opts=ResourceOptions.merge(resource_options, route_table_resource_opts)
        )

        self.olvpc_subnets: List[ec2.Subnet] = []
        zones: List[Text] = availability_zones(vpc_config.region)
        v6net = self.olvpc.ipv6_cidr_block.apply(
            lambda cidr: [str(net) for net in IPv6Network(cidr).subnets(new_prefix=SUBNET_PREFIX_V6)])
        subnet_iterator = zip(
            range(vpc_config.num_subnets),
            cycle(zones),
            vpc_config.cidr_block.subnets(new_prefix=SUBNET_PREFIX_V4),
            v6net)
        for index, zone, subnet_v4, subnet_v6 in subnet_iterator:
            net_name = f'{vpc_config.vpc_name}-subnet-{index + 1}'
            subnet_resource_opts, imported_subnet_id = subnet_opts(subnet_v4)
            if imported_subnet_id:
                subnet = ec2.get_subnet(id=imported_subnet_id)
                zone = subnet.availability_zone
            ol_subnet = ec2.Subnet(
                net_name,
                cidr_block=str(subnet_v4),
                ipv6_cidr_block=subnet_v6,
                availability_zone=zone,
                vpc_id=self.olvpc.id,
                map_public_ip_on_launch=vpc_config.default_public_ip,
                tags=vpc_config.tags,
                assign_ipv6_address_on_creation=vpc_config.enable_ipv6,
                opts=ResourceOptions.merge(resource_options, subnet_resource_opts)
            )
            ec2.RouteTableAssociation(
                f'{net_name}-route-table-association',
                subnet_id=ol_subnet.id,
                route_table_id=self.route_table.id,
                opts=resource_options)
            self.olvpc_subnets.append(ol_subnet)

        self.db_subnet_group = rds.SubnetGroup(
            f'{vpc_config.vpc_name}-db-subnet-group',
            opts=resource_options,
            description=f'RDS subnet group for {vpc_config.vpc_name}',
            name=f'{vpc_config.vpc_name}-db-subnet-group',
            subnet_ids=[net.id for net in self.olvpc_subnets],
            tags=vpc_config.tags)

        ec2.VpcEndpoint(
            f'{vpc_config.vpc_name}-s3',
            service_name='com.amazonaws.us-east-1.s3',
            vpc_id=self.olvpc.id,
            tags=vpc_config.tags,
            opts=ResourceOptions(parent=self))

        self.register_outputs({
            'olvpc': self.olvpc,
            'subnets': self.olvpc_subnets,
            'route_table': self.route_table,
            'rds_subnet_group': self.db_subnet_group
        })


class OLVPCPeeringConnection(ComponentResource):
    """A Pulumi component for creating a VPC peering connection and populating bidirectional routes."""

    def __init__(
            self,
            vpc_peer_name: Text,
            source_vpc: OLVPC,
            destination_vpc: OLVPC,
            opts: Optional[ResourceOptions] = None
    ):
        """Create a peering connection and assocuated routes between two managed VPCs.

        :param vpc_peer_name: The name of the peering connection
        :type vpc_peer_name: Text

        :param source_vpc: The source VPC object to be used as one end of the peering connection.
        :type source_vpc: ec2.Vpc

        :param destination_vpc: The destination VPC object to be used as the other end of the peering connection
        :type destination_vpc: ec2.Vpc

        :param opts: Resource option definitions to propagate to the child resources
        :type opts: ResourceOptions
        """
        super().__init__('ol:infrastructure:aws:VPCPeeringConnection', vpc_peer_name, None, opts)
        resource_options = ResourceOptions.merge(ResourceOptions(parent=self), opts)  # type: ignore
        self.peering_connection = ec2.VpcPeeringConnection(
            f'{source_vpc.vpc_config.vpc_name}-to-{destination_vpc.vpc_config.vpc_name}-vpc-peer',
            auto_accept=True,
            vpc_id=source_vpc.olvpc.id,
            peer_vpc_id=destination_vpc.olvpc.id,
            tags=source_vpc.vpc_config.merged_tags(
                {'Name': f'{source_vpc.vpc_config.vpc_name} to {destination_vpc.vpc_config.vpc_name} peer'}),
            opts=resource_options
        )
        self.source_to_dest_route = ec2.Route(
            f'{source_vpc.vpc_config.vpc_name}-to-{destination_vpc.vpc_config.vpc_name}-route',
            route_table_id=source_vpc.route_table.id,
            destination_cidr_block=destination_vpc.olvpc.cidr_block,
            vpc_peering_connection_id=self.peering_connection.id,
            opts=resource_options
        )
        self.dest_to_source_route = ec2.Route(
            f'{destination_vpc.vpc_config.vpc_name}-to-{source_vpc.vpc_config.vpc_name}-route',
            route_table_id=destination_vpc.route_table.id,
            destination_cidr_block=source_vpc.olvpc.cidr_block,
            vpc_peering_connection_id=self.peering_connection.id,
            opts=resource_options
        )
        self.register_outputs({})
