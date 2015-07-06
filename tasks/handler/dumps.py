import os
import io
import urllib
import webapp2
import logging
import json
import csv
import pickle

import httplib2
from google.appengine.api import memcache
from google.appengine.ext import ndb
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials
from apiclient.http import MediaIoBaseUpload
from mapper.mapper_async import AsyncMapper

from models import LogEmail, RecipientQueueData
import tasks
import settings


class DumperHandler(webapp2.RequestHandler):
  def post(self):
    schedule_urlsafe = self.request.get('urlsafe')
    dump_type = self.request.get('dump_type')
    schedule = ndb.Key(urlsafe=schedule_urlsafe).get()

    if schedule:
      tasks_queue_name = ['recipient-queue-data-mapper']

      if dump_type == 'unsend':
        object_name = '{}-{}-unsend-dump.csv'.format(schedule.subject.encode('utf8'),
                                                     schedule.category.encode('utf8'))
        dumper = FailWorkerDumper(schedule.key, tasks_queue_name, object_name)
        tasks.addTask(tasks_queue_name, dumper.run)

      elif dump_type == 'send':
        object_name = '{}-{}-logemail-dump.csv'.format(schedule.subject.encode('utf8'),
                                                       schedule.category.encode('utf8'))
        dumper = LogEmailDumper(schedule.key, tasks_queue_name, object_name)
        tasks.addTask(tasks_queue_name, dumper.run)


class FailWorkerDumper(AsyncMapper):
  KIND = RecipientQueueData

  # set max execute time less than 500
  # avoid io.BytesIO hit memory limit
  MAX_EXECUTION_TIME = 200

  def __init__(self, schedule_key, tasks_queue, filename):
    super(FailWorkerDumper, self).__init__()
    self.FILTERS = [
      (RecipientQueueData.schedule_key, schedule_key),
      (RecipientQueueData.status, 'fail_worker')
    ]
    self.schedule_key = schedule_key
    self.tasks_queue = tasks_queue

    self.filename = filename
    self.is_header_write = False
    self.writer = None
    self.fh = io.BytesIO()
    self.exclude = ['hr', 'ii', 'gi']

    self.chunks = 0
    self.count = 0
    self.sourceObjects = []

  def map_fn(self, items):
    self.count += len(items)
    for item in items:
      for recipient in json.loads(item.data):
        if not self.writer:
          self.writer = csv.DictWriter(self.fh, filter(lambda x: not self.exclude.__contains__(x), recipient.keys()))

        if not self.is_header_write:
          self.writer.writeheader()
          self.is_header_write = True

        self.writer.writerow({k: v for k, v in recipient.items() if not self.exclude.__contains__(k)})

      n = ndb.Future('yo dawg')
      n.set_result('yo')
      yield n

  def enqueue(self, next_cursor):
    self.writer = None
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  def finish(self, more):
    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    gcs_service = build('storage', 'v1', http=http, developerKey=settings.DEVELOPER_KEY)

    if more:
      name, ext = os.path.splitext(self.filename)

      media = MediaIoBaseUpload(self.fh, mimetype='text/plain', chunksize=1024 * 1024, resumable=True)
      object_name = 'dump/{}-{:d}.txt'.format(name, self.chunks)
      object_resource = {
        'name': object_name
      }
      req = gcs_service.objects().insert(bucket=settings.BUCKET, body=object_resource, media_body=media)
      req.execute()

      self.chunks += 1
      self.fh = io.BytesIO()
      self.sourceObjects.append({'name': object_name})

    else:
      if self.sourceObjects:
        composite_object_resource = {
          'contentType': 'text/plain'
        }

        compose_req_body = {
          'sourceObjects': self.sourceObjects,
          'destination': composite_object_resource
        }

        req = gcs_service.objects().compose(
          destinationBucket=settings.BUCKET,
          destinationObject='dump/{}'.format(self.filename),
          body=compose_req_body)
        req.execute()

        schedule = self.schedule_key.get()
        schedule.unsend_recipients_log = '/{0}/{1}'.format(settings.BUCKET,
                                                           urllib.quote('dump/{}'.format(self.filename)))
        schedule.put()

        # delete chunks
        for object_name in self.sourceObjects:
          gcs_service.objects().delete(bucket=settings.BUCKET,
                                       object=object_name.get('name')).execute()

      else:

        if self.fh.getvalue():
          media = MediaIoBaseUpload(self.fh, mimetype='text/plain', chunksize=1024 * 1024, resumable=True)
          name = 'dump/{}'.format(self.filename)
          object_resource = {
            'name': name
          }
          req = gcs_service.objects().insert(bucket=settings.BUCKET, body=object_resource, media_body=media)
          req.execute()

          schedule = self.schedule_key.get()
          schedule.unsend_recipients_log = '/{0}/{1}'.format(settings.BUCKET,
                                                             urllib.quote('dump/{}'.format(self.filename)))
          schedule.put()

        else:
          logging.info('empty fail tasks, cancel dump')
          return

      logging.info('fail tasks recipeints list dump(%d) ok' % self.count)


class LogEmailDumper(AsyncMapper):
  KIND = LogEmail

  # set max execute time less than 500
  # avoid io.BytesIO hit memory limit
  MAX_EXECUTION_TIME = 200

  def __init__(self, schedule_key, tasks_queue, filename):
    super(LogEmailDumper, self).__init__()
    self.FILTERS = [(LogEmail.schedule_key, schedule_key)]
    self.schedule_key = schedule_key
    self.tasks_queue = tasks_queue

    self.filename = filename
    self.is_header_write = False
    self.exclude = ['hr', 'ii', 'gi']
    self.writer = None
    self.fh = io.BytesIO()

    self.chunks = 0
    self.count = 0
    self.sourceObjects = []

  def map_fn(self, items):
    self.count += len(items)
    for item in map(
        lambda item: pickle.loads(item.csv_properties) if item.csv_properties else dict(email=item.to), items):

      if not self.writer:
        self.writer = csv.DictWriter(self.fh, filter(lambda x: not self.exclude.__contains__(x), item.keys()))

      if not self.is_header_write:
        self.writer.writeheader()
        self.is_header_write = True

      self.writer.writerow({k: v for k, v in item.items() if not self.exclude.__contains__(k)})
      n = ndb.Future('yo dawg')
      n.set_result('yo')
      yield n

  def enqueue(self, next_cursor):
    self.writer = None
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  def finish(self, more):
    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    gcs_service = build('storage', 'v1', http=http, developerKey=settings.DEVELOPER_KEY)

    if more:
      name, ext = os.path.splitext(self.filename)

      media = MediaIoBaseUpload(self.fh, mimetype='text/plain', chunksize=1024 * 1024, resumable=True)
      object_name = 'dump/{}-{:d}.txt'.format(name, self.chunks)
      object_resource = {
        'name': object_name
      }
      req = gcs_service.objects().insert(bucket=settings.BUCKET, body=object_resource, media_body=media)
      req.execute()

      self.chunks += 1
      self.fh = io.BytesIO()
      self.sourceObjects.append({'name': object_name})

    else:
      if self.sourceObjects:
        composite_object_resource = {
          'contentType': 'text/plain'
        }

        compose_req_body = {
          'sourceObjects': self.sourceObjects,
          'destination': composite_object_resource
        }

        req = gcs_service.objects().compose(
          destinationBucket=settings.BUCKET,
          destinationObject='dump/{}'.format(self.filename),
          body=compose_req_body)
        req.execute()

        schedule = self.schedule_key.get()
        schedule.send_recipients_log = '/{0}/{1}'.format(settings.BUCKET,
                                                         urllib.quote('dump/{}'.format(self.filename)))
        schedule.put()

        # delete chunks
        for object_name in self.sourceObjects:
          gcs_service.objects().delete(bucket=settings.BUCKET,
                                       object=object_name.get('name')).execute()

      else:

        if self.fh.getvalue():
          media = MediaIoBaseUpload(self.fh, mimetype='text/plain', chunksize=1024 * 1024, resumable=True)
          name = 'dump/{}'.format(self.filename)
          object_resource = {
            'name': name
          }
          req = gcs_service.objects().insert(bucket=settings.BUCKET, body=object_resource, media_body=media)
          req.execute()

          schedule = self.schedule_key.get()
          schedule.send_recipients_log = '/{0}/{1}'.format(settings.BUCKET,
                                                           urllib.quote('dump/{}'.format(self.filename)))
          schedule.put()

        else:
          logging.info('empty logEmail, cancel dump')
          return

      logging.info('logEmail dump(%d) ok' % self.count)
