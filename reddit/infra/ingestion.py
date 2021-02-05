import os.path
from infra.collector import CollectorLayer
from infra.datalake import DataLakeLayer
from infra.networking import NetworkingLayer

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_iam as iam,
    aws_logs as logs,
    aws_kinesis as k,
    aws_elasticsearch as es,
    aws_kinesisfirehose as f,
)

prod_buffering_hints = f.CfnDeliveryStream.BufferingHintsProperty(
  interval_in_seconds=900,
  size_in_m_bs=128)

debug_buffering_hints = f.CfnDeliveryStream.BufferingHintsProperty(
  interval_in_seconds=60,
  size_in_m_bs=1)

buffering_hints=debug_buffering_hints

class ESDelivery(core.Construct):
    """
    Configure the data collections layer
    """

    def __init__(
            self, scope: core.Construct, id: str,
            kinesis: k.Stream,
            domain: es.Domain,
            bucket: s3.Bucket,
            role: iam.Role,
            log_group: logs.LogGroup,
            networking:NetworkingLayer,
            index_name: str,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)       

        subnets = networking.vpc.select_subnets(subnet_group_name='Collector').subnet_ids
        self.log_stream = logs.LogStream(self,'LogStream',
          log_group=log_group,
          log_stream_name='ESD-'+index_name,
          removal_policy= core.RemovalPolicy.DESTROY)        

        # Load data into Elastic Search
        self.elastic_delivery = f.CfnDeliveryStream(
            self, 'ElasticDelivery',
            delivery_stream_type='KinesisStreamAsSource',
            kinesis_stream_source_configuration=f.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=kinesis.stream_arn,
                role_arn= role.role_arn,
            ),
            elasticsearch_destination_configuration=f.CfnDeliveryStream.ElasticsearchDestinationConfigurationProperty(
                index_name=index_name,
                s3_backup_mode='AllDocuments',
                domain_arn=domain.domain_arn,
                role_arn= role.role_arn,
                vpc_configuration= f.CfnDeliveryStream.VpcConfigurationProperty(
                  role_arn= role.role_arn,
                  security_group_ids= [ networking.security_group.security_group_id],
                  subnet_ids=subnets,
                ),
                s3_configuration=f.CfnDeliveryStream.S3DestinationConfigurationProperty(
                    bucket_arn= bucket.bucket_arn,
                    role_arn= role.role_arn,
                    buffering_hints=buffering_hints,
                    cloud_watch_logging_options=f.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                        enabled=True,
                        log_group_name=log_group.log_group_name,
                        log_stream_name=self.log_stream.log_stream_name),
                    error_output_prefix='errors/',
                    prefix=index_name + '/incoming/')))


class IngestionLayer(core.Construct):
    """
    Configure the data collections layer
    """

    def __init__(self, scope: core.Construct, id: str, collector: CollectorLayer, datalake: DataLakeLayer,networking:NetworkingLayer, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Configure the role
        self.role = iam.Role(
            self, 'Role',
            assumed_by=iam.ServicePrincipal(service='firehose.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    managed_policy_name='AmazonKinesisReadOnlyAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                  managed_policy_name='AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    managed_policy_name='AmazonESFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    managed_policy_name='AmazonEC2FullAccess')
            ],
            description='Role for ES Delivery Stream')

        # Configure the intermediate bucket
        self.ingestion_bucket = s3.Bucket(
            self, 'IngestionBucket',
            removal_policy=core.RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                  abort_incomplete_multipart_upload_after=core.Duration.days(7),
                  expiration=core.Duration.days(365)
                )])

        # Configure Logging
        self.log_group = logs.LogGroup(
            self, 'LogGroup',
            removal_policy=core.RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_MONTH)

        self.security_group = networking.security_group

        ESDelivery(
            self, 'Submissions',
            kinesis=collector.submission_stream,
            bucket=self.ingestion_bucket,
            role=self.role,
            log_group = self.log_group,
            domain=datalake.search,
            networking=networking,
            index_name='submissions')

        ESDelivery(
            self, 'Comments',
            kinesis=collector.comment_stream,
            bucket=self.ingestion_bucket,
            role=self.role,
            log_group = self.log_group,
            domain=datalake.search,
            networking=networking,
            index_name='comments')
