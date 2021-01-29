from infra.vpce import VpcEndpointsForAWSServices
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_elasticsearch as es,
    aws_logs as logs,
    aws_kms as kms,
    aws_iam as iam,
)


class NetworkingLayer(core.Construct):
    """
    Configure the networking layer
    """

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self, 'Vpc',
            cidr='10.0.0.0/16',
            enable_dns_hostnames=True,
            enable_dns_support=True,
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                  name='Public', subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(
                  name='Collector', subnet_type=ec2.SubnetType.PRIVATE, cidr_mask=24),
            ])

        #VpcEndpointsForIsolatedSubnets(self,'Endpoints',vpc=self.vpc)

        self.security_group = ec2.SecurityGroup(
            self, 'SecurityGroup',
            vpc=self.vpc,
            allow_all_outbound=True,
            description='Data Lake Security Group')

        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(cidr_ip=self.vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic(),
            description='Allow any traffic from within vpc')

        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(cidr_ip='74.102.88.0/24'),
            connection=ec2.Port.all_traffic(),
           description='Jersey City Verizon')