# -*- coding: utf-8 -*-

__author__ = 'cage'

import os
import logging

if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
  DEBUG = True
else:
  DEBUG = False

logging.info("Starting application in DEBUG mode: %s", DEBUG)

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')

ADMINS = [
  'cage@mitac.com.tw',
  'sunnyhu@mitac.com.tw',
  'simonsu@mitac.com.tw'
]

SITE_NAME = 'cheerspoint'
BASIC_SITE_URL = 'https://mitac-cheerspoint-v20150518.appspot.com/'
SITE_OWNER = 'KAI CHU CHUNG'
DISQUS_SHORTNAME = 'cheerspoint'


