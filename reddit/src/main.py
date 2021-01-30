from json import dumps
from datetime import datetime
from scaper import Scraper
from writer import StreamWriter

scraper = Scraper(subreddit='wallstreetbets')
submission_writer = StreamWriter(stream_name='RedditSync-CollectorSubmissionOutput436F4C20-RtvwYoK7f4Kp')

# top_level_comments = scraper.fetch_comments(submission_id='l4xxjm')
# total=0
# for tlc in top_level_comments:
#   for tree in tlc:
#     #print(dumps(tree, indent=True))
#     total += 1
# print('Found: '+total)


for year in range(2021,2013,-1):
  print('=================')
  print(year)
  print('=================')

  start_time = int(datetime(year, 1, 1).timestamp())
  end_time = int(datetime(year, 1, 30).timestamp())

  submissions = scraper.fetch_submissions(
    start_time=start_time, 
    end_time=end_time)

  submission_writer.put_records(submissions)

  # for submission in scraper.fetch_submissions(
  #   start_time=start_time, 
  #   end_time=end_time):

  #   # Dump the message...
  #   print(dumps(submission,indent=True))
  #   submission_writer.put_records([submission])
