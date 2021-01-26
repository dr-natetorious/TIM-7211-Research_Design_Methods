from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_elasticsearch as es,
    aws_logs as logs,
    aws_kms as kms,
    aws_iam as iam,
)


class DataLakeLayer(core.Construct):
    """
    Configure the data collections layer
    """

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self, 'DataLake',
            cidr='10.0.0.0/16',
            enable_dns_hostnames=True,
            enable_dns_support=True,
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                  name='Public', subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(
                    name='Private', subnet_type=ec2.SubnetType.PRIVATE, cidr_mask=20)
            ])

        self.security_group = ec2.SecurityGroup(
            self, 'DataLakeSecurityGroup',
            vpc=self.vpc,
            allow_all_outbound=True,
            description='Data Lake Security Group')

        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(cidr_ip=self.vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic(),
            description='Allow any traffic from within vpc')

        self.encryption_key = kms.Key(
            self, 'DataLakeKey',
            removal_policy=core.RemovalPolicy.DESTROY,
            enable_key_rotation=True)

        self.search = es.Domain(
            self, 'Search',
            version=es.ElasticsearchVersion.V7_9,
            enforce_https=True,
            node_to_node_encryption=True,
            encryption_at_rest=es.EncryptionAtRestOptions(
                enabled=True,
                kms_key=self.encryption_key
            ),
            vpc_options=es.VpcOptions(
                subnets=[self.vpc.private_subnets[0]],
                security_groups=[self.security_group]
            ),
            logging=es.LoggingOptions(
                app_log_enabled=True,
                app_log_group=logs.LogGroup(
                    self, 'SearchAppLogGroup',
                    removal_policy=core.RemovalPolicy.DESTROY,
                    retention=logs.RetentionDays.ONE_MONTH),
                audit_log_enabled=True,
                audit_log_group=logs.LogGroup(
                    self, 'SearchAuditLogs',
                    removal_policy=core.RemovalPolicy.DESTROY,
                    retention=logs.RetentionDays.ONE_MONTH),
                slow_index_log_enabled=True,
                slow_index_log_group=logs.LogGroup(
                    self, 'SearchSlowIndex',
                    removal_policy=core.RemovalPolicy.DESTROY,
                    retention=logs.RetentionDays.ONE_MONTH),
            ),
            fine_grained_access_control=es.AdvancedSecurityOptions(
                master_user_name='wsbscraper',
                master_user_password=core.SecretValue.plain_text(
                    secret='D3generate!')
            ))

        # Configre the LinkedServiceRole to update the VPC
        serviceLinkedRole = core.CfnResource(
            self, 'LinkedServiceRole',
            type="AWS::IAM::ServiceLinkedRole",
            properties={
                'AWSServiceName': "es.amazonaws.com",
                'Description': "Role for ES to access resources in my VPC"
            })
        self.search.node.add_dependency(serviceLinkedRole)
