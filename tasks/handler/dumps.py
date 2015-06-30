import os
import io
import webapp2
import logging

import httplib2
from google.appengine.api import memcache
from google.appengine.ext import ndb
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials
from apiclient.http import MediaIoBaseUpload
from mapper.mapper_async import AsyncMapper

from models import LogEmail
import tasks
import settings


class LogEailDumperHandler(webapp2.RequestHandler):
  def post(self):
    schedule_urlsafe = self.request.get('urlsafe')
    logging.info('schedule_urlsafe: %s' % schedule_urlsafe)
    schedule = ndb.Key(urlsafe=schedule_urlsafe).get()

    if schedule:
      tasks_queue_name = ['recipient-queue-data-mapper']
      object_name = '{}-{}-logemail-dump.txt'.format(schedule.subject.encode('utf8'), schedule.category.encode('utf8'))
      dumper = LogEmailDumper(schedule.key, tasks_queue_name, object_name)
      tasks.addTask(tasks_queue_name, dumper.run)


class LogEmailDumper(AsyncMapper):
  KIND = LogEmail

  def __init__(self, schedule_key, tasks_queue, filename):
    super(LogEmailDumper, self).__init__()
    self.FILTERS = [(LogEmail.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

    self.filename = filename
    self.fh = io.BytesIO()

    self.chunks = 0
    self.sourceObjects = []

  def map_fn(self, items):
    for item in items:
      self.fh.write(item.to.encode('utf-8') + '\n')

      n = ndb.Future('yo dawg')
      n.set_result('yo')
      yield n

  def enqueue(self, next_cursor):
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
      req = gcs_service.objects().insert(bucket="cheerspoint-recipient", body=object_resource, media_body=media)
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
          destinationBucket="cheerspoint-recipient",
          destinationObject='dump/{}'.format(self.filename),
          body=compose_req_body)
        resp = req.execute()

      else:

        if self.fh.getvalue():
          media = MediaIoBaseUpload(self.fh, mimetype='text/plain', chunksize=1024 * 1024, resumable=True)
          name = 'dump/{}'.format(self.filename)
          object_resource = {
            'name': name
          }
          req = gcs_service.objects().insert(bucket="cheerspoint-recipient", body=object_resource, media_body=media)
          req.execute()

          self.fh = io.BytesIO()

        else:
          logging.info('empty logEmail, cancel dump')

      logging.info('logEmail dump ok')
