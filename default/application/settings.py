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

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')

WEB_CLIENT_ID = '24182559640-juv18blbdckri5rsp4ik0e0th9v5lfph.apps.googleusercontent.com'

DEVELOPER_KEY = 'AIzaSyAtxMdn2Da20CQIRzWueYEejehJFyBXl2s'

ADMINS = [
  'cage@mitac.com.tw',
  'sunnyhu@mitac.com.tw',
  'simonsu@mitac.com.tw'
]

SITE_NAME = 'cheerspoint'
BASIC_SITE_URL = 'https://mitac-cheerspoint-v20150518.appspot.com/'
SITE_OWNER = 'KAI CHU CHUNG'
DISQUS_SHORTNAME = 'cheerspoint'

# recipient upload bucket
BUCKET = 'cheerspoint-recipient'

cheerspoint_api = endpoints.api(name='cheerspoint',
                                version='v1',
                                description='cheerspoint',
                                allowed_client_ids=[WEB_CLIENT_ID,
                                                    endpoints.API_EXPLORER_CLIENT_ID],
                                scopes=[endpoints.EMAIL_SCOPE])