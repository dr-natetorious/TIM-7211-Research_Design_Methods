import os.path
from aws_cdk import (
  core,
  aws_ec2 as ec2,
  aws_sqs as sqs,
  aws_lambda as lambda_,
  aws_ecr_assets as assets,
  aws_lambda_event_sources as events,
  aws_stepfunctions as sf,
  aws_stepfunctions_tasks as t,
  aws_logs as logs,
  aws_kinesis as k,
)

src_root_dir = os.path.join(os.path.dirname(__file__),"../src")
repository_name = 'reddit-sync'
layer_subnets=ec2.SubnetSelection(subnet_group_name='Collector')

class SyncStateMachineConstruct(core.Construct):
  """
  Configure the data collections layer
  """
  def __init__(self, scope: core.Construct, id: str, definition:sf.Chain, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)
    
    self.states = sf.StateMachine(self,'StateMachine',
      definition= definition,
      logs= sf.LogOptions(
        destination= logs.LogGroup(self,'LogGroup',
        removal_policy=core.RemovalPolicy.DESTROY,
        retention=logs.RetentionDays.ONE_MONTH),
        include_execution_data=True,
        level= sf.LogLevel.ALL),
      state_machine_type= sf.StateMachineType.STANDARD,
      timeout=core.Duration.days(1),
      tracing_enabled=True)

class CollectorLayer(core.Construct):
  """
  Configure the data collections layer
  """
  def __init__(self, scope: core.Construct, id: str, vpc:ec2.Vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)
    
    self.vpc = vpc

    self.create_lambda_functions()
    self.create_kinesis()
    self.create_step_function()

  @property
  def submission_stream(self) -> k.Stream:
    return self.__submission_stream

  @property
  def comment_stream(self) -> k.Stream:
    return self.__comment_stream
  
  def create_lambda_functions(self):
    self.repo = assets.DockerImageAsset(self,'Repo',
      directory=src_root_dir,
      repository_name=repository_name)

    self.sync_lambda = lambda_.DockerImageFunction(self,'ContainerFunction',
      code = lambda_.DockerImageCode.from_ecr(
        repository=self.repo.repository,
        tag=self.repo.image_uri.split(':')[-1]), # lambda_.DockerImageCode.from_image_asset(directory=os.path.join(src_root_dir,directory)),
      description='Python container lambda function for '+repository_name,
      timeout= core.Duration.minutes(1),
      memory_size=512,
      tracing= lambda_.Tracing.ACTIVE,
      vpc= self.vpc,
      vpc_subnets=layer_subnets)

  def create_kinesis(self):
    self.__submission_stream = k.Stream(self,'SubmissionOutput',
      retention_period= core.Duration.days(1),
      shard_count=1)
    self.sync_lambda.add_environment('SUBMISSION_STREAM',self.submission_stream.stream_name)
    self.submission_stream.grant_write(self.sync_lambda.role)

    self.__comment_stream = k.Stream(self,'CommentOutput',
      retention_period= core.Duration.days(1),
      shard_count=1)
    self.sync_lambda.add_environment('COMMENT_STREAM', self.comment_stream.stream_name)
    self.comment_stream.grant_write(self.sync_lambda.role)
    
  def create_step_function(self) -> sf.StateMachine:
    run_sync_task = t.LambdaInvoke(
      self,'RunSync',
      lambda_function= self.sync_lambda)

    is_complete = sf.Choice(self,'Is-Complete'
      ).when(sf.Condition.string_equals('$.is_done', 'False'), run_sync_task
      ).otherwise(sf.Pass(self,'Finished'))

    definition = run_sync_task.next(is_complete)
    SyncStateMachineConstruct(self,'Sync', definition=definition)
