from infra.collector import CollectorLayer
from infra.datalake import DataLakeLayer

def create_layers(scope):
  return [
    DataLakeLayer(scope,'DataLake'),
    CollectorLayer(scope,'Collector'),
  ]