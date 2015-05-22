"""
Models the data that is stored in the datastore (NDB) and retrieved from it
"""

from google.appengine.ext import ndb


class FlexWebhook(ndb.Expando):
  created = ndb.DateTimeProperty(auto_now_add=True)