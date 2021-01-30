from os import environ
from json import dumps
from datetime import datetime, timedelta
from scaper import Scraper
from incoming_request import IncomingRequest
from writer import StreamWriter

submission_writer = StreamWriter(environ.get('SUBMISSION_STREAM'))
comment_writer = StreamWriter(environ.get('COMMENT_STREAM'))

def handle_event(event,context):
  scraper = Scraper(subreddit='wallstreetbets')
  year = 2020
  print('=================')
  print(year)
  print('=================')

  incoming_request = IncomingRequest(event)

  start_time = int(datetime(year, 1, 1).timestamp())
  end_time = int(datetime(year, 1, 30).timestamp())

  print(dumps({
    'incoming_request':{
      'start': incoming_request.start_time.timestamp(),
      'end': incoming_request.end_time.timestamp()
    },
    'static':{
      'start': start_time,
      'end': end_time
    }
  }, indent=True))

  submissions = scraper.fetch_submissions(
    start_time=start_time, 
    end_time=end_time)
    
  submission_writer.put_records([submissions])
  return dumps(incoming_request.increment(),indent=True)

  # for submission in scraper.fetch_submissions(
  #   start_time=start_time, 
  #   end_time=end_time):

  #   # Dump the message...
  #   print(dumps(submission,indent=True))
  #   submission_writer.put_records([submission])
