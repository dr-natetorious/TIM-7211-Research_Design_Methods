from json import dumps
from datetime import datetime, timedelta

date_format='%Y-%m-%d %H:%M:%S'
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
    return datetime.strptime(self.event['start_time'],date_format)

  @property
  def end_time(self) -> datetime:
    return datetime.strptime(self.event['end_time'], date_format)

  @property
  def interval(self) -> timedelta:
    return timedelta(hours=1)

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

  def decrement(self)->dict:
    next_start = self.start_time - self.interval
    return {
      'subreddit': self.subreddit,
      'start_time': next_start.strftime(date_format),
      'end_time': self.end_time.strftime(date_format),
      'is_done': self.start_time.year < 2012
    }
