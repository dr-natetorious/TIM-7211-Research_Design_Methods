import datetime as dt
import typing
from json import dumps
from praw import Reddit
from praw.models import Comment
from praw.models.comment_forest import CommentForest, MoreComments
from psaw import PushshiftAPI

class Scraper:

    def __init__(self, subreddit:str='wallstreetbets'):
      self.reddit = Reddit()
      self.psapi = PushshiftAPI(r=self.reddit)

      self.subreddit = self.reddit.subreddit('wallstreetbets')

    @staticmethod
    def sanitize(s) -> str:
      ret=''
      for c in s:
        if 32 <= ord(c) and ord(c) <= 126:
          ret += c
      return ret

    @staticmethod
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

    @staticmethod
    def default_text(x, default):
      try:
        return x()
      except:
        return default

    def fetch_submissions(self, start_time, end_time) -> typing.List[dict]:
      """
      start_time = int(dt.datetime(year, 1, 1).timestamp())
      end_time = int(dt.datetime(year, 1, 30).timestamp())    
      submissions = scraper.fetch_period(start_time, end_time)
      """
      for submission in self.psapi.search_submissions(
        after=start_time, 
        before=end_time, 
        subreddit='wallstreetbets',
        limit=999):

        if submission.selftext == '[removed]':
          continue
        if submission.selftext == '[deleted]':
          continue

        # Dump the message...
        yield {
          'id': submission.id,
          'created_utc': submission.created_utc,
          'all_awarding':submission.all_awardings,
          'edited': submission.edited,
          'author':{
            'id': Scraper.default_text(lambda: submission.author.fullname, 'unknown'),
            'name':Scraper.default_text(lambda:submission.author.name, 'unknown'),
          },
          'subreddit':{
            'id': submission.subreddit_id,
            'name': submission.subreddit_name_prefixed,
          },
          'mod':{
            'note': submission.mod_note,
            'reason_by':submission.mod_reason_by,
            'reason_title':submission.mod_reason_title,
          },
          'body':submission.selftext,
          'distinguished': submission.distinguished,
          'total_awards_received': submission.total_awards_received,
          'link_flair_text': submission.link_flair_text,
          'score': submission.score,
          'stats':{
            'up': submission.ups,
            'down': submission.downs,
            'upvote_ratio': submission.upvote_ratio,
            'view_count': submission.view_count,
          },
          'title':submission.title,
          'url': submission.url,
          'images': Scraper.images(submission)
        }

    def fetch_comments(self, submission_id:str) -> typing.List[dict]:
      """
      start_time = int(dt.datetime(year, 1, 1).timestamp())
      end_time = int(dt.datetime(year, 1, 30).timestamp())    
      submissions = scraper.fetch_period(start_time, end_time)
      """
      submission = self.reddit.submission(id=submission_id)
      for c in submission.comments:
        print('Top level comment {}'.format(c.id))
        yield self._process_comment(c, submission_id)

    def _process_comment(self, comment, submission_id) -> typing.List[dict]:
      """
      Processes the comment tree
      """
      items =[]
      if isinstance(comment, CommentForest) or isinstance(comment, Comment):
        for reply in comment.replies:
          items.extend(self._process_comment(reply, submission_id))
      elif isinstance(comment, MoreComments):
        for reply in comment.comments(update=True):
          items.extend(self._process_comment(reply, submission_id))
        return items

      this_record= {
        'id': comment.id,
        'created_utc': comment.created_utc,
        'body': comment.body,
        'structure':{
          'parent': comment.parent_id,
          'submission_id':submission_id,
          'depth': comment.depth,
        },
        'author':{
            'id': Scraper.default_text(lambda: comment.author.fullname, 'unknown'),
            'name':Scraper.default_text(lambda:comment.author.name, 'unknown'),
          },
          'subreddit':{
            'id': comment.subreddit_id,
            'name': comment.subreddit_name_prefixed,
          },
          'mod':{
            'note': comment.mod_note,
            'reason_by':comment.mod_reason_by,
            'reason_title':comment.mod_reason_title,
          },
          'stats':{
            'score': comment.score,
            'total_awards_received': comment.total_awards_received,
            'ups': comment.ups,
            'downs':comment.downs,
            'distinguished': comment.distinguished
          }
      }

      items.append(this_record)
      return items
