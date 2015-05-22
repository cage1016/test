import httplib2
from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials


DEVELOPER_KEY = 'AIzaSyAtxMdn2Da20CQIRzWueYEejehJFyBXl2s'

# google cloud storage download chucks size
CHUNKSIZE = 2 * 1024 * 1024

# ipwarmup schedule multiple put size
QUEUE_CHUNKS_SIZE = 50

# recipient upload bucket
BUCKET = 'cheerspoint-recipient'

SENDGRID = {
  'USERNAME': 'kaichu',
  'PASSWORD': '@75dkyz9n'
}


def ValidateGCSWithCredential(function):
  def _decorated(self, *args, **kwargs):
    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    self.gcs_service = build('storage', 'v1', http=http, developerKey=DEVELOPER_KEY)
    return function(self, *args, **kwargs)

  return _decorated