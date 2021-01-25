import os.path
from aws_cdk import (
  core,
  aws_sqs as sqs,
  aws_lambda as lambda_,
  aws_ecr_assets as assets,
  aws_lambda_event_sources as events,
)

src_root_dir = os.path.join(os.path.dirname(__file__),"../src")
repository_name = 'wsbscraper'

class CollectorLayer(core.Construct):
  """
  Configure the data collections layer
  """
  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    self.queue = sqs.Queue(self,'PendingItems',
      fifo=False,
      retention_period= core.Duration.days(14),
      visibility_timeout=core.Duration.minutes(1))

    self.repo = assets.DockerImageAsset(self,'Repo',
      directory=src_root_dir,
      repository_name=repository_name)

    self.function = lambda_.DockerImageFunction(self,'ContainerFunction',
      code = lambda_.DockerImageCode.from_ecr(
        repository=self.repo.repository,
        tag=self.repo.image_uri.split(':')[-1]), # lambda_.DockerImageCode.from_image_asset(directory=os.path.join(src_root_dir,directory)),
      description='Python container lambda function for '+repository_name,
      timeout= core.Duration.minutes(1),
      tracing= lambda_.Tracing.ACTIVE,
    )

    self.function.add_event_source(events.SqsEventSource(
      queue=self.queue,
      batch_size=1))