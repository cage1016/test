import pickle
import webapp2
import logging
import time

from google.appengine.ext import ndb
from datastore_utils import page_queries
from models import ReTry

from utils import timeit, enqueue_task
from mimail_client import MiMailClient

import settings
import tasks


class RetryCheckHandler(webapp2.RequestHandler):
  def get(self):
    if ReTry.query().get() is not None:
      enqueue_task(url='/tasks/retry_resend', queue_name='retry-resend')


class RetrySendWorkHandler(webapp2.RequestHandler):
  @ndb.toplevel
  def post(self):
    queries = [
      ReTry.query().order(ReTry.created)
    ]
    countdown_sec = 0
    for retries in page_queries(queries, fetch_page_size=10, keys_only=False):
      mimail_client = MiMailClient()
      tasks.addTask(['retry-resend'],
                    mimail_client.resend,
                    retries=retries,
                    countdown_sec=countdown_sec,
                    _countdown=countdown_sec)

      countdown_sec += 1
