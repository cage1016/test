# coding: utf-8

import sys
import logging
import pickle
from delorean import Delorean
from validate_email import validate_email

from google.appengine.ext import ndb
from google.appengine import runtime
from google.appengine.api import urlfetch_errors
from google.appengine.api.taskqueue import taskqueue
from google.appengine.runtime.apiproxy_errors import OverQuotaError

from sendgrid import SendGridError, SendGridClientError, SendGridServerError
from sendgrid import SendGridClient
from sendgrid import Mail

from models import LogEmail, LogFailEmail, ReTry
from utils import replace_edm_csv_property, enqueue_task
from datastore_utils import pop_future_done

import settings


class MiMailClient(object):
  def __init__(self, sendgrid_account=None, sendgrid_password=None):
    self.sg = SendGridClient(sendgrid_account, sendgrid_password, raise_errors=True)
    self.futures = []
    self.sender = 'sendgrid'


  def set_sendgrid_client(self, sendgrid_account, sendgrid_password):
    self.sg = SendGridClient(sendgrid_account, sendgrid_password, raise_errors=True)

  def send(self, schedule, content, recipients):

    for recipient in recipients:
      d = Delorean()

      # prepare log data
      log = {}
      log.update(
        schedule_key=schedule.key,
        sender=self.sender,
        category=schedule.category,
        to=recipient['email'],
        reply_to=schedule.reply_to,
        sender_name=schedule.sender_name,
        sender_email=schedule.sender_email,
        subject=schedule.subject,
        body=replace_edm_csv_property(content, recipient, schedule.replace_edm_csv_property),
        schedule_timestamp=schedule.schedule_timestamp,
        schedule_display=schedule.schedule_display,
        when_timestamp=d.epoch(),
        when_display=d.naive(),
        sendgrid_account=schedule.sendgrid_account
      )

      is_valid = validate_email(log.get('to'))
      if not is_valid:
        log.update(reason='manual check: email(%s) is not valid.' % log.get('to'))
        self.save_fail(log)
        continue

      message = Mail()
      message.set_subject(log.get('subject'))
      message.set_html(log.get('body'))
      message.set_from('%s <%s>' % (log.get('sender_name'), log.get('sender_email')))
      if log.get('reply_to'):
        message.set_replyto(log.get('reply_to'))
      message.add_to(log.get('to'))
      message.add_category(log.get('category'))

      self._send(message, log)

    ndb.Future.wait_all(self.futures)

  def resend(self, retries):
    """
    handle resend fail email
    :param queries:
    :return:
    """

    retries_keys = [retry.key for retry in retries]
    for fail_log in ndb.get_multi([retry.failEmail for retry in retries]):
      sendgrid = settings.SENDGRID[fail_log.sendgrid_account]

      self.set_sendgrid_client(sendgrid['USERNAME'], sendgrid['PASSWORD'])

      # prepare log data
      log = {}
      log.update(
        fail_log_key=fail_log.key,
        sender=self.sender,
        category=fail_log.category,
        to=fail_log.to,
        reply_to=fail_log.reply_to,
        sender_name=fail_log.sender_name,
        sender_email=fail_log.sender_email,
        subject=fail_log.subject,
        body=fail_log.body,
        schedule_timestamp=fail_log.schedule_timestamp,
        schedule_display=fail_log.schedule_display,
        when_timestamp=fail_log.when_timestamp,
        when_display=fail_log.when_display,
        sendgrid_account=fail_log.sendgrid_account
      )

      message = Mail()
      message.set_subject(log.get('subject'))
      message.set_html(log.get('body'))
      message.set_from('%s <%s>' % (log.get('sender_name'), log.get('sender_email')))
      if log.get('reply_to'):
        message.set_replyto(log.get('reply_to'))
      message.add_to(log.get('to'))
      message.add_category(log.get('category'))

      self._send(message, log)

    if self.futures:
      ndb.Future.wait_all(self.futures)
      pop_future_done(self.futures)

    if retries_keys:
      enqueue_task(url='/tasks/retry_delete',
                   params={
                     'retries_keys': pickle.dumps(retries_keys)
                   },
                   queue_name='retry-delete')

  def _send(self, message, log):
    try:
      if settings.DEBUG and False:
        status = 200
        msg = ''

        raise Exception('An error occured while connecting to the server: Unable to fetch URL: https://api.sendgrid.com:443/api/mail.send.json')
      else:
        status, msg = self.sg.send(message)

      if status == 200:
        self.save(log)

      else:
        log.update(reason=msg)
        self.save_fail(log)

    except SendGridClientError:
      logging.error('4xx error: %s' % msg)
      log.update(reason=msg)
      self.save_fail(log)

    except SendGridServerError:
      logging.error('5xx error: %s' % msg)
      log.update(reason=msg)
      self.save_fail(log)

    except SendGridError:
      logging.error('error: %s' % msg)
      log.update(reason=msg)
      self.save_fail(log)

    except (
        taskqueue.Error,
        runtime.DeadlineExceededError,
        urlfetch_errors.DeadlineExceededError,
        runtime.apiproxy_errors.CancelledError,
        runtime.apiproxy_errors.DeadlineExceededError,
        runtime.apiproxy_errors.OverQuotaError) as e:

      logging.error('error: %s' % e.message)

      log.update(reason=e.message)
      self.save_fail(log)

    except:
      type, e, traceback = sys.exc_info()
      logging.error('sys.exc_info error: %s' % e.message)

      log.update(reason=e.message)
      self.save_fail(log)


  def save(self, log):
    log_email = LogEmail(
      parent=log.get('schedule_key'),
      sender=log.get('sender'),
      category=log.get('category'),
      to=log.get('to'),
      reply_to=log.get('reply_to'),
      sender_name=log.get('sender_name'),
      sender_email=log.get('sender_email'),
      subject=log.get('subject'),
      body=log.get('body'),
      schedule_timestamp=log.get('schedule_timestamp'),
      schedule_display=log.get('schedule_display'),
      when_timestamp=log.get('when_timestamp'),
      when_display=log.get('when_display'),
      sendgrid_account=log.get('sendgrid_account')
    )
    if log.get('fail_log_key'):
      log_email.fails_link.append(log.get('fail_log_key'))

    self.futures.extend(ndb.put_multi_async([log_email]))

  def save_fail(self, log):
    log_fail_email = LogFailEmail(
      parent=log.get('schedule_key'),
      sender=log.get('sender'),
      category=log.get('category'),
      to=log.get('to'),
      reply_to=log.get('reply_to'),
      sender_name=log.get('sender_name'),
      sender_email=log.get('sender_email'),
      subject=log.get('subject'),
      body=log.get('body'),
      schedule_timestamp=log.get('schedule_timestamp'),
      schedule_display=log.get('schedule_display'),
      when_timestamp=log.get('when_timestamp'),
      when_display=log.get('when_display'),
      sendgrid_account=log.get('sendgrid_account'),
      reason=log.get('reason')
    )
    self.futures.extend(ndb.put_multi_async([log_fail_email]))
    logging.info('%s send fail: %s' % (log.get('to'), log.get('reason')))