# -*- coding: utf-8 -*-

__author__ = 'cage'

import os
import logging
import endpoints

if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
  DEBUG = True
else:
  DEBUG = False

logging.info("Starting application in DEBUG mode: %s", DEBUG)

# endpoint api
if DEBUG:
  API_ROOT = 'http://localhost:8080/_ah/api'
else:
  API_ROOT = 'https://cage-20160705-edm.appspot.com/_ah/api'

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')

WEB_CLIENT_ID = '591130412399-rj4b59imkhhpei2kgirq9frklfplnpec.apps.googleusercontent.com'

DEVELOPER_KEY = 'AIzaSyCe1PxvzGZYMkqlCOaClwM2V5MJfmvh7zg'

SERVICE_ACCOUNT_EMAIL = 'mail-522@cage-20160705-edm.iam.gserviceaccount.com'

ADMINS = [
  'cage.chung@gmail.com',
]

SENDGRID = {
  'USERNAME': 'kaichu',
  'PASSWORD': '@75dkyz9n'
}

SITE_NAME = 'cheerspoint'
BASIC_SITE_URL = 'https://cage-20160705-edm.appspot.com/'
SITE_OWNER = 'KAI CHU CHUNG'
DISQUS_SHORTNAME = 'cheerspoint'

# recipient upload bucket
BUCKET = 'cage-20160705-edm.appspot.com'

cheerspoint_api = endpoints.api(name='cheerspoint',
                                version='v1',
                                description='cheerspoint',
                                allowed_client_ids=[WEB_CLIENT_ID,
                                                    endpoints.API_EXPLORER_CLIENT_ID],
                                scopes=[endpoints.EMAIL_SCOPE])