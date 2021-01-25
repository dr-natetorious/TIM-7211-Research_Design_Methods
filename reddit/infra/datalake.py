from aws_cdk import (
  core,
)

class DataLakeLayer(core.Construct):
  """
  Configure the data collections layer
  """
  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)
