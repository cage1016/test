import os
from apiclient.errors import HttpError
import httplib2
from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials


if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
  DEBUG = True
else:
  DEBUG = False

DEVELOPER_KEY = 'AIzaSyAtxMdn2Da20CQIRzWueYEejehJFyBXl2s'

# google cloud storage download chucks size
# default 1 * 1024 * 1024 (1MB)
CHUNKSIZE = 1 * 1024 * 1024

# ipwarmup schedule multiple put size
QUEUE_CHUNKS_SIZE = 15

# RecipientQueueData query fetch page size
RECIPIENT_CHENKS_SIZE = 10

# html content memcache limit time
# 7200 sec = 2 hours
EDM_CONTENT_MEMCACHE_TIME = 7200

# tasksqueue re-add time limited
# csv_parser & schedule delete
MAX_TASKSQUEUE_EXECUTED_TIME = 500

# recipient upload bucket
BUCKET = 'cheerspoint-recipient'

# SENDGRID = {
# 'USERNAME': 'kaichu',
# 'PASSWORD': '@75dkyz9n'
# }

SENDGRID = {
  'kaichu': {
    'USERNAME': 'kaichu',
    'PASSWORD': '@75dkyz9n',
  },
  'mitac2hr': {
    'USERNAME': 'mitac-2hr',
    'PASSWORD': 'Micloud@mitac888',
  },
  'mitacmax': {
    'USERNAME': 'mitac-max',
    'PASSWORD': 'Micloud@mitac888'
  },
  'mitacwarmup1': {
    'USERNAME': 'mitac-warmup1',
    'PASSWORD': 'Micloud@mitac888'
  },
  'mitacwarmup2': {
    'USERNAME': 'mitac-warmup2',
    'PASSWORD': 'Micloud@mitac888'
  },
  'mitacsymphox': {
    'USERNAME': 'mitac-symphox',
    'PASSWORD': 'Micloud@mitac168'
  }
}