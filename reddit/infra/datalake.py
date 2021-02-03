from infra.networking import NetworkingLayer
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
    def __init__(self, scope: core.Construct, id: str, networking:NetworkingLayer, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.encryption_key = kms.Key(
            self, 'EncryptionKey',
            removal_policy=core.RemovalPolicy.DESTROY,
            enable_key_rotation=True)

        policy = iam.PolicyStatement(
            sid='Allow-by-IPAddress',
            actions=['es:*'],
            principals=[iam.AnyPrincipal()],
            resources=['*'])

        # policy.add_condition('IpAddress',{
        #     'aws:SourceIp':'74.102.88.0/24'
        # })
            
        self.search = es.Domain(
            self, 'SearchCluster',
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
            vpc_options=es.VpcOptions(
                subnets=networking.vpc.public_subnets,
                security_groups=[networking.security_group]
            ),
            logging=es.LoggingOptions(
                app_log_enabled=True,
                app_log_group=logs.LogGroup(
                    self, 'SearchAppLogGroup',
                    removal_policy=core.RemovalPolicy.DESTROY,
                    retention=logs.RetentionDays.ONE_MONTH),
                audit_log_enabled=False,
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
            access_policies=[
                policy              
            ])

        # Configre the LinkedServiceRole to update the VPC
        serviceLinkedRole = core.CfnResource(
            self, 'LinkedServiceRole',
            type="AWS::IAM::ServiceLinkedRole",
            properties={
                'AWSServiceName': "es.amazonaws.com",
                'Description': "Role for ES to access resources in my VPC"
            })
        self.search.node.add_dependency(serviceLinkedRole)
