# coding: utf8

import io
import pickle
import webapp2
import logging
import json

from delorean import Delorean

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from apiclient.http import MediaIoBaseDownload

import settings
from models import Schedule, RecipientQueueData

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