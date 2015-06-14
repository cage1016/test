# coding: utf8

import io
import pickle
from google.appengine.ext.db import TransactionFailedError
import webapp2
import logging
import json

from delorean import Delorean

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from apiclient.http import MediaIoBaseDownload

import settings
from models import Schedule, RecipientQueueData, LogEmail, LogFailEmail

from utils import enqueue_task

from mimail_client import MiMailClient


class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    now = Delorean().truncate('minute')

    logging.info('match schedule_timestamp query = %f' % now.epoch())

    if settings.DEBUG:
      jobs = Schedule.query(Schedule.schedule_timestamp == 1432634400.0, Schedule.error == None).fetch()

    else:
      jobs = Schedule.query(Schedule.schedule_timestamp == now.epoch(), Schedule.error == None).fetch()

    for job in jobs:
      logging.info('job schedule found!!, categroy:%s, hour_capacity= %d' % (job.category, job.hour_capacity))
      enqueue_task(url='/tasks/mailer',
                   params={
                     'jkey': job.key.urlsafe()
                   },
                   queue_name='mailer')


class MailerHandler(webapp2.RequestHandler):
  def read_edm_file(self, edm_object_name):
    data = memcache.get(edm_object_name)
    if data is not None:
      return data

    else:
      fh = io.BytesIO()
      request = self.gcs_service.objects().get_media(bucket=settings.BUCKET, object=edm_object_name.encode('utf8'))
      downloader = MediaIoBaseDownload(fh, request, chunksize=settings.CHUNKSIZE)
      done = False
      while not done:
        status, done = downloader.next_chunk()
        if status:
          logging.info('Download %d%%.' % int(status.progress() * 100))
        logging.info('Download %s Complete!' % edm_object_name)

      data = fh.getvalue()
      memcache.add(edm_object_name, data, settings.EDM_CONTENT_MEMCACHE_TIME)
      return data

  @settings.ValidateGCSWithCredential
  def post(self):
    skey = self.request.get('jkey')

    schedule_job = ndb.Key(urlsafe=skey).get()
    schedule_job.schedule_executed = True
    schedule_job.put()

    if schedule_job:
      logging.info('execute %s @ %s' % (schedule_job.category, schedule_job.schedule_display))

      content = self.read_edm_file(schedule_job.edm_object_name)
      sendgrid = settings.SENDGRID[schedule_job.sendgrid_account]

      cursor = None
      while True:
        curs = Cursor(urlsafe=cursor)
        recipientQueues, next_curs, more = RecipientQueueData.query(
          ancestor=schedule_job.key).fetch_page(settings.QUEUE_CHUNKS_SIZE, start_cursor=curs)

        for index, r in enumerate(recipientQueues):
          params = {
            'schedule': pickle.dumps(schedule_job),
            'recipient_queue': r.data,
            'content': content,
            'edm_object_name': schedule_job.edm_object_name,
            'sendgrid_account': sendgrid['USERNAME'],
            'sendgrid_password': sendgrid['PASSWORD']
          }

          if index % 2 == 0:
            enqueue_task(url='/tasks/worker', queue_name='worker', params=params)

          if index % 2 == 1:
            enqueue_task(url='/tasks/worker2', queue_name='worker2', params=params)

        if more and next_curs:
          cursor = next_curs.urlsafe()

        else:
          break


class WorkHandler(webapp2.RequestHandler):
  def post(self):
    """
    mailsend worker
    """

    schedule = pickle.loads(self.request.get('schedule'))
    content = self.request.get('content')
    recipients = json.loads(self.request.get('recipient_queue'))
    sendgrid_account = self.request.get('sendgrid_account')
    sendgrid_password = self.request.get('sendgrid_password')

    logging.debug('/tasks/worker executed: send %d recipients.' % len(recipients))
    logging.debug(
      'sendgrid_account: %s, subject:%s, category: %s' % (sendgrid_account, schedule.subject, schedule.category))
    logging.debug(recipients)

    mimail_client = MiMailClient(sendgrid_account, sendgrid_password)
    mimail_client.send(schedule, content, recipients)


class SuccessLogSaveHandler(webapp2.RequestHandler):
  @ndb.toplevel
  def post(self):
    log = pickle.loads(self.request.get('log'))

    try:
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

      yield ndb.put_multi_async([log_email])

    except TransactionFailedError as e:
      logging.info('%s, %s, %s: %s. manual re-add to success-log-save queue' % (
        log.get('subject'), log.get('category'), log.get('to'), e.message))

      enqueue_task(url='/tasks/success_log_save',
                   params={'log': pickle.dumps(log)},
                   queue_name='success-log-save')


class FailLogSaveHandler(webapp2.RequestHandler):
  @ndb.toplevel
  def post(self):
    log = pickle.loads(self.request.get('log'))

    try:

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

      logging.info('%s send fail: %s' % (log.get('to'), log.get('reason')))
      yield ndb.put_multi_async([log_fail_email])

    except TransactionFailedError as e:
      logging.info('%s, %s, %s: %s. manual re-add to fail-log-save queue' % (
        log.get('subject'), log.get('category'), log.get('to'), e.message))

      enqueue_task(url='/tasks/fail_log_save',
                   params={'log': pickle.dumps(log)},
                   queue_name='fail-log-save')