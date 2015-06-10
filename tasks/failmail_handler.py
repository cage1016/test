import pickle
import webapp2
import logging
import sys
import time
from delorean import Delorean

from google.appengine import runtime
from google.appengine.api import urlfetch_errors
from google.appengine.ext import ndb
from google.appengine.api.taskqueue import taskqueue
from google.appengine.runtime.apiproxy_errors import OverQuotaError

from sendgrid import SendGridError, SendGridClientError, SendGridServerError
from sendgrid import SendGridClient
from sendgrid import Mail

from models import LogSendEmailFail, LogEmail
import settings

from datastore_utils import page_queries, pop_future_done
from utils import timeit, enqueue_task


class FailMailCheckHandler(webapp2.RequestHandler):
  def get(self):
    if LogSendEmailFail.query().get() is not None:
      enqueue_task(url='/tasks/fail_resend', queue_name='failmail-resend')


class FailMailResendWorkHandler(webapp2.RequestHandler):
  @ndb.toplevel
  @timeit
  def post(self):

    queries = [
      LogSendEmailFail.query()
    ]

    self.futures = []
    for fail_emails in page_queries(queries, fetch_page_size=50, keys_only=False):
      for fail_email in fail_emails:
        d = Delorean()
        sendgrid = settings.SENDGRID[fail_email.sendgrid_account]

        sg = SendGridClient(sendgrid['USERNAME'], sendgrid['PASSWORD'], raise_errors=True)

        message = Mail()
        message.set_subject(fail_email.subject)
        message.set_html(fail_email.body)
        message.set_from('%s <%s>' % (fail_email.sender_name, fail_email.sender_email))
        if fail_email.reply_to:
          message.set_replyto(fail_email.reply_to)
        message.add_to(fail_email.to)
        message.add_category(fail_email.category)

        try:
          # status = 200
          # msg = ''
          status, msg = sg.send(message)

          if status == 200:
            self.save_log_email(fail_email, d)

          else:
            self.save_fail_log_email(fail_email, d, msg)

        except SendGridClientError:
          logging.error('4xx error: %s' % msg)
          self.save_fail_log_email(fail_email, d, msg)

        except SendGridServerError:
          logging.error('5xx error: %s' % msg)
          self.save_fail_log_email(fail_email, d, msg)

        except SendGridError:
          logging.error('error: %s' % msg)
          self.save_fail_log_email(fail_email, d, msg)

        except (
            taskqueue.Error,
            runtime.DeadlineExceededError,
            urlfetch_errors.DeadlineExceededError,
            runtime.apiproxy_errors.CancelledError,
            runtime.apiproxy_errors.DeadlineExceededError,
            runtime.apiproxy_errors.OverQuotaError) as e:

          logging.error('error: %s' % e)
          self.save_fail_log_email(fail_email, d, e)

        except:
          type, e, traceback = sys.exc_info()
          logging.error('sys.exc_info error: %s' % e)

          self.save_fail_log_email(fail_email, d, e)

      if self.futures:
        ndb.Future.wait_all(self.futures)
        pop_future_done(self.futures)

      if fail_emails:
        enqueue_task(url='/tasks/failmail_delete',
                     params={
                       'keys': pickle.dumps([f.key for f in fail_emails])
                     },
                     queue_name='failmail-delete')

      if (time.time() - self.ts).__int__() > settings.MAX_TASKSQUEUE_EXECUTED_TIME:
        enqueue_task(url='/tasks/fail_resend',
                     queue_name='failmail-resend')
        break

  def save_log_email(self, fail_email, d):
    log_email = LogEmail(
      sender='sendgrid',
      category=fail_email.category,
      to=fail_email.to,
      reply_to=fail_email.reply_to,
      sender_name=fail_email.sender_name,
      sender_email=fail_email.sender_email,
      subject=fail_email.subject,
      body=fail_email.body,
      schedule_timestamp=fail_email.schedule_timestamp,
      schedule_display=fail_email.schedule_display,
      when_timestamp=d.epoch(),
      when_display=d.naive(),
      action='resend',
      sendgrid_account=fail_email.sendgrid_account
    )
    self.futures.extend(ndb.put_multi_async([log_email]))

  def save_fail_log_email(self, fail_email, d, error_msg):
    log_send_mail_fail = LogSendEmailFail(
      sender='sendgrid',
      category=fail_email.category,
      to=fail_email.to,
      reply_to=fail_email.reply_to,
      sender_name=fail_email.sender_name,
      sender_email=fail_email.sender_email,
      subject=fail_email.subject,
      body=fail_email.body,
      schedule_timestamp=fail_email.schedule_timestamp,
      schedule_display=fail_email.schedule_display,
      when_timestamp=d.epoch(),
      when_display=d.naive(),
      reason=str(error_msg),
      sendgrid_account=fail_email.sendgrid_account
    )

    self.futures.extend(ndb.put_multi_async([log_send_mail_fail]))
    logging.info('%s re send fail: %s' % (fail_email.to, str(error_msg)))


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