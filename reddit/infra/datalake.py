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
    Configure the datalake layer
    """

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.encryption_key = kms.Key(
            self, 'EncryptionKey',
            removal_policy=core.RemovalPolicy.DESTROY,
            enable_key_rotation=True)

        self.search = es.Domain(
            self, 'Search',
            version=es.ElasticsearchVersion.V7_9,
            enforce_https=True,
            node_to_node_encryption=True,
            capacity= es.CapacityConfig(
              #master_nodes=3,
              #warm_nodes=len(self.vpc.availability_zones),
              data_nodes= 2 # len(self.vpc.availability_zones),              
            ),
            zone_awareness= es.ZoneAwarenessConfig(
              availability_zone_count= 2 #len(self.vpc.availability_zones)
            ),
            encryption_at_rest=es.EncryptionAtRestOptions(
                enabled=True,
                kms_key=self.encryption_key
            ),
            # vpc_options=es.VpcOptions(
            #     subnets=self.vpc.public_subnets,
            #     security_groups=[self.security_group]
            # ),
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
                master_user_name='reddit',
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
