"""
Models the data that is stored in the datastore (NDB) and retrieved from it
"""
import re

from google.appengine.ext import ndb

PATTERN = r'<(.*)>'


class CheerspointWebhook(ndb.Expando):
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def new(cls, chunks):
    webhook = CheerspointWebhook()
    webhook.populate(**chunks)
    return webhook

  def _pre_put_hook(self):
    if self._properties.get('smtp-id'):
      smtp_id = self.__getattr__('smtp-id')

      self.__delattr__('smtp-id')
      self.__setattr__('smtp_id', re.search(PATTERN, smtp_id).group(1))