"""
Models the data that is stored in the datastore (NDB) and retrieved from it
"""
import re

from google.appengine.ext import ndb

PATTERN = r'<(.*)>'


class FlexWebhook(ndb.Expando):
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def new(cls, chunks):
    webhook = FlexWebhook()
    webhook.populate(**chunks)
    return webhook

  def _pre_put_hook(self):
    if self._properties.get('smtp-id'):
      self.__setattr__('smtp-id', re.search(PATTERN, self.__getattr__('smtp-id')).group(1))