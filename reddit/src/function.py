from json import dumps
from datetime import datetime, timedelta
from scaper import Scraper

class IncomingRequest:
  """
  Represents the incomding event structure
  """
  def __init__(self, event):
    self.event = event

  @property
  def subreddit(self) -> str:
    return self.event['subreddit']

  @property
  def start_time(self) -> datetime:
    return datetime.strptime(self.event['start_time'],'%Y-%m-%d')

  @property
  def end_time(self) -> datetime:
    return datetime.strptime(self.event['end_time'],'%Y-%m-%d')

  @property
  def is_done(self) -> bool:
    return self.__is_done

  @is_done.setter
  def is_done(self,value)->None:
    self.__is_done = value

  def __str__(self)->str:
    return dumps({
      'subreddit': self.subreddit,
      'start_time': str(self.start_time),
      'end_time': str(self.end_time),
    }, indent=True)

  def increment(self)->dict:
    next_start = self.start_time + timedelta(days=1)
    return {
      'subreddit': self.subreddit,
      'start_time': next_start,
      'end_time': self.end_time,
      'is_done': next_start > self.end_time
    }

def handle_event(event, context):
  """
  The main entry point for Lambda Function.
  """
  incoming_request = IncomingRequest(event)
  print(str(incoming_request))

  scraper = Scraper(subreddit=incoming_request.subreddit)

  submissions = scraper.fetch_submissions(
    start_time= incoming_request.start_time.timestamp(),
    end_time=incoming_request.end_time.timestamp())

  print("Found {} submissions".format(len(list(submissions))))
  return incoming_request.increment()