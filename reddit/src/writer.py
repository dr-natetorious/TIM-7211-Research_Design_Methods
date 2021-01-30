from  boto3 import client
from typing import List
from json import dumps
from uuid import uuid4

# 75% of 5MB
MAX_SIZE = 5 * 1024 * 1024 * .75

class StreamWriter:

  def __init__(self, stream_name:str):
    """
    Initialize a new instance of the stream writer
    """
    self.stream_name = stream_name
    self.client = client('kinesis')

  def put_records(self, messages:List[dict]) -> dict:
    """
    Post messages to the stream.
    """
    records=[]
    size=0
    for message in messages:
      print('{}({}): {}'.format(message['id'],message['created_utc'],message['title']))
      data = dumps(message,indent=True).encode()

      # Check if there is enough buffered messages
      if size + len(data) > MAX_SIZE:
        self.__send(records)
        records.clear()
        size =0
      
      # Add another message to the list
      records.append({
        'Data': data,
        'PartitionKey': str(uuid4())
      })

    # Flush the buffer if required
    if len(records) > 0:
      self.__send(records)

  def __send(self, records:List[dict]):
    """
    Write the buffered records
    """
    response = self.client.put_records(
      Records=records,
      StreamName=self.stream_name
    )

    print("Sent {} records: {}".format(
      len(records),
      dumps(response)
    ))
