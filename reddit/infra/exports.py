from infra.collector import CollectorLayer
from infra.datalake import DataLakeLayer
from infra.ingestion import IngestionLayer

def create_layers(scope):
  
  datalake = DataLakeLayer(scope,'DataLake')
  collector = CollectorLayer(scope,'Collector')
  ingestion = IngestionLayer(scope,'Ingestion', collector=collector, datalake=datalake)

  return [
    datalake,
    collector,
    ingestion
  ]