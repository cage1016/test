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


class RetryCheckHandler(webapp2.RequestHandler):
  def get(self):
    if ReTry.query().get() is not None:
      enqueue_task(url='/tasks/retry_resend', queue_name='retry-resend')


class RetrySendWorkHandler(webapp2.RequestHandler):
  @ndb.toplevel
  @timeit
  def post(self):
    queries = [
      ReTry.query().order(ReTry.created)
    ]

    mimail_client = MiMailClient()

    for retries in page_queries(queries, fetch_page_size=10, keys_only=False):
      mimail_client.resend(retries)

      if (time.time() - self.ts).__int__() > settings.MAX_TASKSQUEUE_EXECUTED_TIME:
        enqueue_task(url='/tasks/retry_resend',
                     queue_name='retry-resend')
        break


class RetryDeleteWorkHandler(webapp2.RequestHandler):
  @ndb.toplevel
  def post(self):
    retries_keys = pickle.loads(self.request.get('retries_keys'))
    yield ndb.delete_multi_async(keys=retries_keys)