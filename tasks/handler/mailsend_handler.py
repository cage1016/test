# coding: utf8
import csv

import io
import json
import logging
import datetime

import webapp2
import httplib2
from google.appengine.api import memcache
from google.appengine.ext import ndb
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials
from apiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from delorean import Delorean
from datastore_utils import incremental_map
from mapper.mapper import Mapper
from mapper.mapper_async import AsyncMapper
from mimail_client import MiMailClient2
from models import Schedule, RecipientQueueData
import settings
import tasks

import random


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

      # mailer2 = Mailer2(job.key, ['mailer'])
      # tasks.addTask(['mailer'], mailer2.run)

      mailer2_async = Mailer2Async(job.key, ['mailer'])
      tasks.addTask(['mailer'], mailer2_async.run)


class Mailer2(Mapper):
  KIND = RecipientQueueData

  def __init__(self, schedule_key, tasks_queue):
    super(Mailer2, self).__init__()
    self.FILTERS = [(RecipientQueueData.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

    self.count = 0
    self.success_worker = 0
    self.fail_worker = 0
    self.schedule_key = schedule_key
    self.schedule_job = schedule_key.get()

    self.content = self.read_edm_file(self.schedule_job.edm_object_name)
    self.sendgrid = settings.SENDGRID[self.schedule_job.sendgrid_account]

    # update schedule sharding count name
    self.sharding_count_name = '{}-{:f}'.format(self.schedule_job.category, self.schedule_job.schedule_timestamp)
    self.schedule_job.sharding_count_name = self.sharding_count_name
    self.schedule_job.status = 'running'
    self.schedule_job.put()

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

  def __map(self, entity):
    """
    Debug only
    """
    countdown_sec = self.count // settings.QUEUE_CHUNKS_SIZE

    mimail_client2 = MiMailClient2(self.sendgrid['USERNAME'], self.sendgrid['PASSWORD'])

    if random.choice([True] * 10 + [False] * 5):
      r = tasks.addTask(['worker', 'worker2'],
                        mimail_client2.run,
                        schedule=self.schedule_job,
                        content=self.content,
                        recipient_queues=entity,
                        sharding_count_name=self.sharding_count_name,
                        _countdown=countdown_sec).get_result()
    else:
      r = False

    if r:
      self.success_worker += 1
      return ([], [])

    else:
      self.fail_worker += 1
      entity.status = 'fail_worker'
      return ([entity], [])

  def map(self, entity):
    countdown_sec = self.count // settings.QUEUE_CHUNKS_SIZE

    mimail_client2 = MiMailClient2(self.sendgrid['USERNAME'], self.sendgrid['PASSWORD'])

    r = tasks.addTask(['worker', 'worker2'],
                      mimail_client2.run,
                      schedule=self.schedule_job,
                      content=self.content,
                      recipient_queues=entity,
                      sharding_count_name=self.sharding_count_name,
                      _countdown=countdown_sec).get_result()

    self.count += 1
    if r:
      self.success_worker += 1
      return ([], [])

    else:
      self.fail_worker += 1
      entity.status = 'fail_worker'
      return ([entity], [])

  def finish(self):
    self.schedule_job.success_worker = self.success_worker
    self.schedule_job.fail_worker = self.fail_worker
    self.schedule_job.put()

    logging.info('mailer2 finished. \ncount(%d), \nsuccess_worker(%d), \nfail_worker(%d)' % (
      self.count, self.success_worker, self.fail_worker))

    if self.fail_worker > 0:
      b = bbb(self.schedule_key, self.schedule_job.sharding_count_name)
      tasks.addTask(self.tasks_queue, b.run)

  def enqueue(self, start_key, batch_size):
    new_mapper = Mailer2(self.schedule_key, self.tasks_queue)
    tasks.addTask(self.tasks_queue, new_mapper._continue, start_key, batch_size)


class Mailer2Async(AsyncMapper):
  KIND = RecipientQueueData

  def __init__(self, schedule_key, tasks_queue):
    super(Mailer2Async, self).__init__()
    self.FILTERS = [(RecipientQueueData.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

    self.success_worker = 0
    self.fail_worker = 0
    self.schedule_key = schedule_key
    self.schedule_job = schedule_key.get()

    self.content = self.read_edm_file(self.schedule_job.edm_object_name)
    self.sendgrid = settings.SENDGRID[self.schedule_job.sendgrid_account]

    # update schedule sharding count name
    d = self.schedule_job.created + datetime.timedelta(hours=8)
    self.sharding_count_name = '{}-{}'.format(self.schedule_job.category, d.strftime('%Y-%m-%d %H:%M:%S+08:00'))
    self.schedule_job.sharding_count_name = self.sharding_count_name
    self.schedule_job.status = 'running'
    self.schedule_job.put()

    self.count = 0

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

  def finish(self, more):
    self.schedule_job.success_worker = self.success_worker
    self.schedule_job.fail_worker = self.fail_worker
    self.schedule_job.put()

    if more:
      logging.info(
        'mailer2 async run end and continue have\'t finished mailer dispatch , \ncount(%d), success_worker(%d), fail_worker(%d)' % (
          (self.success_worker + self.fail_worker), self.success_worker, self.fail_worker))

    else:
      logging.info('mailer2 async finished. \ncount(%d), success_worker(%d), fail_worker(%d)' % (
        (self.success_worker + self.fail_worker), self.success_worker, self.fail_worker))

      if self.fail_worker > 0:
        b = bbb(self.schedule_key, self.schedule_job.sharding_count_name)
        tasks.addTask(self.tasks_queue, b.run)

  def enqueue(self, next_cursor):
    # new_mapper = Mailer2Async(self.schedule_key, self.tasks_queue)
    # tasks.addTask(self.tasks_queue, new_mapper._continue, c)
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  def map_fn(self, entities):
    mimail_client2 = MiMailClient2(self.sendgrid['USERNAME'], self.sendgrid['PASSWORD'])
    for entity in entities:
      self.count += 1
      countdown_sec = self.count // settings.QUEUE_CHUNKS_SIZE
      r = tasks.addTask(['worker', 'worker2'],
                        mimail_client2.run,
                        schedule=self.schedule_job,
                        content=self.content,
                        recipient_queues=entity,
                        sharding_count_name=self.sharding_count_name,
                        _countdown=countdown_sec).get_result()

      if r:
        self.success_worker += 1
        n = ndb.Future('yo dawg')
        n.set_result('yo')
        yield n

      else:
        self.fail_worker += 1
        entity.status = 'fail_worker'
        entity.put_async()
        yield entity


class bbb(object):
  def __init__(self, schedule_key, filename):
    self.schedule_key = schedule_key
    self.filename = filename
    self.is_header_write = False
    self.writer = None
    self.fh = io.BytesIO()
    self.exclude = ['hr', 'ii', 'gi']

  def map_fn(self, items):
    for item in items:
      for recipient in json.loads(item.data):
        if not self.is_header_write:
          self.writer = csv.DictWriter(self.fh, filter(lambda x: not self.exclude.__contains__(x), recipient.keys()))
          self.writer.writeheader()
          self.is_header_write = True

        self.writer.writerow({k: v for k, v in recipient.items() if not self.exclude.__contains__(k)})

      n = ndb.Future('yo dawg')
      n.set_result('yo')
      yield n

  def run(self):

    query = [
      RecipientQueueData.query(RecipientQueueData.schedule_key == self.schedule_key,
                               RecipientQueueData.status == 'fail_worker')
    ]

    finished = incremental_map(query, map_fn=self.map_fn)

    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    gcs_service = build('storage', 'v1', http=http, developerKey=settings.DEVELOPER_KEY)

    media = MediaIoBaseUpload(self.fh, mimetype='text/plain', chunksize=1024 * 1024, resumable=True)
    object_resource = {
      'name': unicode.encode(self.filename, 'utf-8')
    }
    req = gcs_service.objects().insert(bucket="cheerspoint-recipient", body=object_resource, media_body=media)
    req.execute()
    logging.info('upload ok')
