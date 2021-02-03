from infra.collector import CollectorLayer
from infra.datalake import DataLakeLayer
from infra.ingestion import IngestionLayer
from infra.networking import NetworkingLayer

def create_layers(scope):
  
  networking = NetworkingLayer(scope,'Networking')
  datalake = DataLakeLayer(scope,'DataLake', networking=networking)
  collector = CollectorLayer(scope,'Collector', vpc=networking.vpc)
  ingestion = IngestionLayer(scope,'Ingestion', collector=collector, datalake=datalake, networking=networking)

  return [
    networking,
    datalake,
    collector,
    ingestion
  ]