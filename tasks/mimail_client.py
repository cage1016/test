# coding: utf-8

import sys
import logging
import pickle
import json
import random
import operator
from delorean import Delorean
from google.appengine.ext.db import TransactionFailedError

from google.appengine.ext import ndb
from google.appengine import runtime
from google.appengine.api import urlfetch_errors
from google.appengine.api.taskqueue import taskqueue
from google.appengine.runtime.apiproxy_errors import OverQuotaError

from sendgrid import SendGridError, SendGridClientError, SendGridServerError
from sendgrid import SendGridClient
from sendgrid import Mail

from models import LogEmail, LogFailEmail, ReTry, RecipientQueueData
from utils import replace_edm_csv_property

import settings
import random

from google.appengine.api import urlfetch


class MiMailClient2(object):
  def __init__(self, sendgrid_account=None, sendgrid_password=None):
    self.sg = SendGridClient(sendgrid_account, sendgrid_password, raise_errors=True)
    self.sender = 'sendgrid'

    self.to_put = []
    self.to_delete = []

  def set_sendgrid_client(self, sendgrid_account, sendgrid_password):
    self.sg = SendGridClient(sendgrid_account, sendgrid_password, raise_errors=True)

  def success_log(self, schedule, sends, sender):
    list_of_entities = []
    for send in sends:
      log_email = LogEmail(
        schedule_key=schedule.key,
        sender=sender,
        category=schedule.category,
        to=send.get('recipient').get('email'),
        reply_to=schedule.reply_to,
        sender_name=schedule.sender_name,
        sender_email=schedule.sender_email,
        subject=schedule.subject,
        # body=data.get('body'),
        schedule_timestamp=schedule.schedule_timestamp,
        schedule_display=schedule.schedule_display,
        sendgrid_account=schedule.sendgrid_account
      )
      list_of_entities.append(log_email)

    return list_of_entities

  def fail_log(self, schedule, sends, sender, content):
    list_of_entities = []
    for send in sends:
      log_fail_email = LogFailEmail(
        schedule_key=schedule.key,
        sender=sender,
        category=schedule.category,
        to=send.get('recipient').get('email'),
        reply_to=schedule.reply_to,
        sender_name=schedule.sender_name,
        sender_email=schedule.sender_email,
        subject=schedule.subject,
        body=replace_edm_csv_property(content, send.get('recipient'), schedule.replace_edm_csv_property),
        schedule_timestamp=schedule.schedule_timestamp,
        schedule_display=schedule.schedule_display,
        sendgrid_account=schedule.sendgrid_account,
        reason=send.get('msg')
      )
      list_of_entities.append(log_fail_email)

    return list_of_entities

  def success_log_retry(self, sends):
    list_of_entities = []
    for send in sends:
      log_email = LogEmail(
        schedule_key=send.get('fail_log').schedule_key,
        sender=send.get('fail_log').sender,
        category=send.get('fail_log').category,
        to=send.get('fail_log').to,
        reply_to=send.get('fail_log').reply_to,
        sender_name=send.get('fail_log').sender_name,
        sender_email=send.get('fail_log').sender_email,
        subject=send.get('fail_log').subject,
        # body=data.get('body'),
        schedule_timestamp=send.get('fail_log').schedule_timestamp,
        schedule_display=send.get('fail_log').schedule_display,
        sendgrid_account=send.get('fail_log').sendgrid_account
      )
      log_email.fails_link.append(send.get('fail_log').key)

      list_of_entities.append(log_email)

    return list_of_entities

  def fail_log_retry(self, sends):
    list_of_entities = []
    for send in sends:
      log_fail_email = LogFailEmail(
        schedule_key=send.get('fail_log').schedule_key,
        sender=send.get('fail_log').sender,
        category=send.get('fail_log').category,
        to=send.get('fail_log').to,
        reply_to=send.get('fail_log').reply_to,
        sender_name=send.get('fail_log').sender_name,
        sender_email=send.get('fail_log').sender_email,
        subject=send.get('fail_log').subject,
        body=send.get('fail_log').body,
        schedule_timestamp=send.get('fail_log').schedule_timestamp,
        schedule_display=send.get('fail_log').schedule_display,
        sendgrid_account=send.get('fail_log').sendgrid_account,
        reason=send.get('msg')
      )
      list_of_entities.append(log_fail_email)

    return list_of_entities

  def run(self, schedule, content, recipient_queues):
    futures = []
    for recipient in json.loads(recipient_queues.data):
      message = Mail()
      message.set_subject(schedule.subject)
      message.set_html(replace_edm_csv_property(content, recipient, schedule.replace_edm_csv_property))
      message.set_from('%s <%s>' % (schedule.sender_name, schedule.sender_email))
      if schedule.reply_to:
        message.set_replyto(schedule.reply_to)
      message.add_to(recipient.get('email'))
      message.add_category(schedule.category)

      status, msg = self._send(message)
      futures.append(dict(recipient=recipient, status=status, msg=msg))

    send_success = filter(lambda f: f.get('status') == 200, futures)
    send_fail = filter(lambda f: f.get('status') != 200, futures)

    # save success send log
    if send_success:
      self.to_put.extend(self.success_log(schedule, send_success, self.sender))

    # save fail send log
    if send_fail:
      self.to_put.extend(self.fail_log(schedule, send_fail, self.sender, content))

    recipient_queues.status = 'executed'
    self.to_put.append(recipient_queues)

    if self.to_put:
      ndb.put_multi(self.to_put)
      self.to_put = []

  def resend(self, retries):
    futures = []
    for fail_log in ndb.get_multi([retry.failEmail for retry in retries]):
      if not fail_log:
        continue

      sendgrid = settings.SENDGRID[fail_log.sendgrid_account]

      self.set_sendgrid_client(sendgrid['USERNAME'], sendgrid['PASSWORD'])

      log_mail = LogEmail.query(LogEmail.fails_link.IN([fail_log.key])).get()
      if log_mail:
        logging.info('fail mail %s-%s has been retry success.' % (fail_log.subject, fail_log.to))

      else:
        message = Mail()
        message.set_subject(fail_log.subject)
        message.set_html(fail_log.body)
        message.set_from('%s <%s>' % (fail_log.sender_name, fail_log.sender_email))
        if fail_log.reply_to:
          message.set_replyto(fail_log.reply_to)
        message.add_to(fail_log.to)
        message.add_category(fail_log.category)

        status, msg = self._send(message)
        futures.append(dict(fail_log=fail_log, status=status, msg=msg))

    # split log to another task to save
    send_success = filter(lambda f: f.get('status') == 200, futures)
    send_fail = filter(lambda f: f.get('status') != 200, futures)

    if send_success:
      def clear_body(send):
        send.get('fail_log').body = None
        return send

      self.to_put.extend(
        self.success_log_retry(map(clear_body, send_success))
      )

      # retry fail log has been send succes and need to remove
      keys = [r.key for r in
              filter(lambda r: any(s == r.failEmail for s in map(lambda s: s.get('fail_log').key, send_success)),
                     retries)]
      if keys:
        self.to_delete.extend(keys)

    if send_fail:
      self.to_put.extend(self.fail_log_retry(send_fail))

    if self.to_put:
      ndb.put_multi(self.to_put)
      self.to_put = []

    if self.to_delete:
      ndb.delete_multi(self.to_delete)
      self.to_delete = []

  def _foke_http_post(self):

    # result = urlfetch.fetch(url='http://104.154.53.75', method=urlfetch.POST)
    # return result.status_code, result.content

    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, url='http://104.154.53.75', method=urlfetch.POST)

    try:
      result = rpc.get_result()
      # return result.status_code, result.content
      return random.choice([200] * 995 + [400] * 5), result.content
      # return random.choice([200] * 100), result.content

    except urlfetch.DownloadError, e:
      return 400, e.message

  def _send(self, message):
    try:
      if settings.DEBUG or True:
        status, msg = self._foke_http_post()

        # raise Exception('An error occured while connecting to the server: xxxxxx (foke error for debug)')
      else:
        status, msg = self.sg.send(message)

    except (
        taskqueue.Error,
        runtime.DeadlineExceededError,
        urlfetch_errors.DeadlineExceededError,
        runtime.apiproxy_errors.CancelledError,
        runtime.apiproxy_errors.DeadlineExceededError,
        runtime.apiproxy_errors.OverQuotaError) as e:

      msg = e.message
      status = 500

    except:
      type, e, traceback = sys.exc_info()
      logging.debug('sys.exc_info error: %s' % e.message)

      msg = e.message
      status = 500

    return status, msg
