import datetime as dt
from json import dumps
from praw import Reddit
from psaw import PushshiftAPI

reddit = Reddit()

def sanitize(s) -> str:
  ret=''
  for c in s:
    if 32 <= ord(c) and ord(c) <= 126:
      ret += c
  return ret

wsb = reddit.subreddit('wallstreetbets')
for thread in wsb.new(limit=10,):
    title = sanitize(thread.title)
    print(title)

psapi = PushshiftAPI(r=reddit)


def images(submission):
  """
  Attempt to read the media properties.
  """
  lst = []
  try:
    if 'images' in submission.preview:
      for image in submission.preview['images']:
        if image is None:
          break
        lst.append(image['source']['url'])
    return lst

  except AttributeError:
    return []

def default_text(x, default):
  try:
    return x()
  except:
    return default

for year in range(2021,2013,-1):
  print('=================')
  print(year)
  print('=================')

  start_time = int(dt.datetime(year, 1, 1).timestamp())
  end_time = int(dt.datetime(year, 1, 30).timestamp())
  for submission in psapi.search_submissions(
    after=start_time, 
    before=end_time, 
    subreddit='wallstreetbets',
    limit=10):

    if submission.selftext == '[removed]':
      continue
    if submission.selftext == '[deleted]':
      continue

    # Dump the message...
    print(dumps(
      {
        'id': submission.id,
        'created_utc': submission.created_utc,
        'all_awarding':submission.all_awardings,
        'edited': submission.edited,
        'author':{
          'id': default_text(lambda: submission.author.fullname, 'unknown'),
          'name':default_text(lambda:submission.author.name, 'unknown'),
        },
        'selftext':submission.selftext,
        'distinguished': submission.distinguished,
        'link_flair_text': submission.link_flair_text,
        'score': submission.score,
        'title':submission.title,
        'url': submission.url,
        'images': images(submission)
      },indent=True))
