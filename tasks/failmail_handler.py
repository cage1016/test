import pickle
import webapp2
import logging
import time

from google.appengine.ext import ndb
from datastore_utils import page_queries
from models import LogFailEmail

from utils import timeit, enqueue_task
from mimail_client import MiMailClient

import settings


class FailMailCheckHandler(webapp2.RequestHandler):
  def get(self):
    if LogFailEmail.query().get() is not None:
      enqueue_task(url='/tasks/fail_resend', queue_name='failmail-resend')


class FailMailResendWorkHandler(webapp2.RequestHandler):
  @ndb.toplevel
  @timeit
  def post(self):
    queries = [
      LogFailEmail.query()
    ]

    mimail_client = MiMailClient()

    for fail_emails in page_queries(queries, fetch_page_size=50, keys_only=False):
      mimail_client.resend(fail_emails)

      if (time.time() - self.ts).__int__() > settings.MAX_TASKSQUEUE_EXECUTED_TIME:
        enqueue_task(url='/tasks/fail_resend',
                     queue_name='failmail-resend')
        break


class FailMailDeleteWorkHandler(webapp2.RequestHandler):
  @ndb.toplevel
  def post(self):
    keys = pickle.loads(self.request.get('keys'))

    for fail_email in ndb.get_multi(keys=keys):
      logging.info('sendgrid_account: %s, subject: %s, category: %s' % (fail_email.sendgrid_account,
                                                                        fail_email.subject,
                                                                        fail_email.category))
      logging.info('email: %s' % fail_email.to)
      logging.info('retry reason: %s' % fail_email.reason)

      yield ndb.delete_multi_async(keys=keys)