# coding: utf8

import io
import webapp2
import logging
import json

from delorean import Delorean

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from apiclient.http import MediaIoBaseDownload
from google.appengine import runtime
from datastore_utils import Mapper

import settings
from models import Schedule, RecipientQueueData

import tasks

from mimail_client import MiMailClient, MiMailClient2

import httplib2
from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials


class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    now = Delorean().truncate('minute')
    mtime = self.request.get('mtime')

    logging.info('match schedule_timestamp query = %f' % now.epoch())

    if mtime:
      logging.debug('manual fire schedule %s ' % mtime)
      jobs = Schedule.query(Schedule.schedule_timestamp == float(mtime), Schedule.error == None).fetch()

    elif settings.DEBUG:
      jobs = Schedule.query(Schedule.schedule_timestamp == 1432634400.0, Schedule.error == None).fetch()

    else:
      jobs = Schedule.query(Schedule.schedule_timestamp == now.epoch(), Schedule.error == None).fetch()

    for job in jobs:
      logging.info('job schedule found!!, categroy:%s, hour_capacity= %d' % (job.category, job.hour_capacity))

      mailer2 = Mailer2(job.key, ['mailer'])
      tasks.addTask(['mailer'], mailer2.run)


class Mailer2(Mapper):
  KIND = RecipientQueueData

  def __init__(self, schedule_key, tasks_queue):
    super(Mailer2, self).__init__()
    self.FILTERS = [(RecipientQueueData.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

    self.count = 0
    self.success_worker = 0
    self.fail_worker = 0
    self.schedule_job = schedule_key.get()

    self.content = self.read_edm_file(self.schedule_job.edm_object_name)
    self.sendgrid = settings.SENDGRID[self.schedule_job.sendgrid_account]

  def read_edm_file(self, edm_object_name):
    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    gcs_service = build('storage', 'v1', http=http, developerKey=settings.DEVELOPER_KEY)

    data = memcache.get(edm_object_name)
    if data is not None:
      return data

    else:
      fh = io.BytesIO()
      request = gcs_service.objects().get_media(bucket=settings.BUCKET, object=edm_object_name.encode('utf8'))
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

  def map(self, entity):
    countdown_sec = self.count // 10

    mimail_client2 = MiMailClient2(self.sendgrid['USERNAME'], self.sendgrid['PASSWORD'])
    r = tasks.addTask(['worker', 'worker2'],
                      mimail_client2.run,
                      schedule=self.schedule_job,
                      content=self.content,
                      recipient_queues=entity,
                      _countdown=countdown_sec).get_result()

    if r:
      self.success_worker += 1

    else:
      self.fail_worker += 1

    self.count += 1
    return ([], [])

  def finish(self):
    self.schedule_job.success_worker = self.success_worker
    self.schedule_job.fail_worker = self.fail_worker
    self.schedule_job.schedule_executed = True

    self.schedule_job.put()
    logging.info('mailer2 finished. count(%d), success_worker(%d), fail_worker(%d)' % (
      self.count, self.success_worker, self.fail_worker))


class Mailer(object):
  def __init__(self, schedule_key):
    self.schedule_job = schedule_key.get()
    self.futures = []
    self.count = 0

  @settings.ValidateGCSWithCredential
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

  def finish(self):
    """Called when the mapper has finished, to allow for any final work to be done."""
    pass

  def run(self, cursor=None):
    self.schedule_job.schedule_executed = True
    self.schedule_job.put()

    try:

      if self.schedule_job:
        logging.info('execute %s @ %s' % (self.schedule_job.category, self.schedule_job.schedule_display))

        content = self.read_edm_file(self.schedule_job.edm_object_name)
        sendgrid = settings.SENDGRID[self.schedule_job.sendgrid_account]

        countdown_sec = 0
        while True:
          curs = Cursor(urlsafe=cursor)
          recipientQueues, next_curs, more = RecipientQueueData.query(
            RecipientQueueData.schedule_key == self.schedule_job.key).fetch_page(settings.QUEUE_CHUNKS_SIZE,
                                                                                 start_cursor=curs)

          for r in recipientQueues:
            mimail_client = MiMailClient(sendgrid['USERNAME'], sendgrid['PASSWORD'])
            tasks.addTask(['worker', 'worker2'],
                          mimail_client.send,
                          schedule=self.schedule_job,
                          content=content,
                          recipient_queues=r,
                          countdown_sec=countdown_sec,
                          _countdown=countdown_sec)
            self.count += 1

          if more and next_curs:
            cursor = next_curs.urlsafe()
            countdown_sec += 1

          else:
            logging.info('job: %s reciepientQueue (%d) dispatch done.' % (self.schedule_job.subject, self.count))
            break

    except (
        runtime.DeadlineExceededError,
        runtime.apiproxy_errors.CancelledError,
        runtime.apiproxy_errors.DeadlineExceededError,
        runtime.apiproxy_errors.OverQuotaError) as e:

      new_mailer = Mailer(self.schedule_job.key)
      tasks.addTask(['mailer'], new_mailer.run, cursor=cursor)
      return

    self.finish()
