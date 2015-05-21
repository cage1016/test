import httplib2
from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials


DEVELOPER_KEY = 'AIzaSyAtxMdn2Da20CQIRzWueYEejehJFyBXl2s'

CHUNKSIZE = 2 * 1024 * 1024


def ValidateGCSWithCredential(function):
  def _decorated(self, *args, **kwargs):
    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    self.gcs_service = build('storage', 'v1', http=http, developerKey=DEVELOPER_KEY)
    return function(self, *args, **kwargs)

  return _decorated