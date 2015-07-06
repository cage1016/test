import logging

import webapp2
import httplib2
from google.appengine.ext import ndb
from apiclient.errors import HttpError
from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

import settings
from models import RecipientQueueData, ReTry, Schedule, LogEmail, LogFailEmail
from general_counter import GeneralCounterShardConfig, GeneralCounterShard, SHARD_KEY_TEMPLATE
from mapper.mapper_async import AsyncMapper
import tasks


class GCSResourcesDeleteHandler(webapp2.RequestHandler):
  def post(self):
    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    gcs_service = build('storage', 'v1', http=http, developerKey=settings.DEVELOPER_KEY)

    object_name = self.request.get('object_name')
    bucket_name = self.request.get('bucket_name')

    logging.info('delete tasks qeueu: delete gcs: %s/%s' % (bucket_name, object_name))

    try:

      req = gcs_service.objects().delete(bucket=bucket_name, object=object_name.encode('utf8'))
      resp = req.execute()

    except HttpError, error:
      logging.info(error)


class ScheduleDeleteCheckHandler(webapp2.RequestHandler):
  def check_schedule_procress(self, schedule):

    if schedule.delete_mark_ReTry and schedule.delete_mark_logEmail and schedule.delete_mark_LogFailEmail and schedule.delete_mark_RecipientQueueData:
      schedule.key.delete()
      logging.info('delete %s - %s all done (RecipientsQueueData, logEmail, FailLogEmail, Retry)' % (
        schedule.subject, schedule.category))

  def get(self):
    schedules = Schedule.query(Schedule.status == 'deleting').fetch()
    for schedule in schedules:
      self.check_schedule_procress(schedule)


class ScheduleDeleteHandler(webapp2.RequestHandler):
  def post(self):
    """
    delete schedule job. change schedule stat first and start
    to delete the following entities.

    schedule job:
      -> RecipientQueueData
      -> LogEmail
      -> FailLogEmail
      -> Retry

    cron job to check if other entities has been delete
    then delete schedule itself.
    """

    schedule_urlsafe = self.request.get('urlsafe')
    logging.info('schedule_urlsafe: %s' % schedule_urlsafe)
    schedule = ndb.Key(urlsafe=schedule_urlsafe).get()

    if schedule:
      schedule.status = 'deleting'
      schedule.put()

      # delete sharding count
      if schedule.sharding_count_name:
        config = ndb.Key(GeneralCounterShardConfig, schedule.sharding_count_name).get()
        if config:
          shard_key_strings = [SHARD_KEY_TEMPLATE.format(schedule.sharding_count_name, index)
                               for index in range(config.num_shards)]

          ndb.delete_multi([ndb.Key(GeneralCounterShard, shard_key_string) for shard_key_string in shard_key_strings])
          config.key.delete()

        mem_sharding_count = memcache.get(schedule.sharding_count_name)
        if mem_sharding_count:
          memcache.delete(schedule.sharding_count_name)

      mapper_RecipientQueueData = RecipientQueueDataDeleteMapper(schedule.key, ['schedule-delete-mapper'])
      mapper_logEmail = LogEmailDeleteMapper(schedule.key, ['schedule-delete-mapper'])
      mapper_FailLogEmail = LogFailEmailDeleteMapper(schedule.key, ['schedule-delete-mapper'])
      mapper_Retry = RetryDeleteMapper(schedule.key, ['schedule-delete-mapper'])

      tasks.addTask(['schedule-delete-mapper'], mapper_RecipientQueueData.run)
      tasks.addTask(['schedule-delete-mapper'], mapper_logEmail.run)
      tasks.addTask(['schedule-delete-mapper'], mapper_FailLogEmail.run)
      tasks.addTask(['schedule-delete-mapper'], mapper_Retry.run)


class RetryDeleteMapper(AsyncMapper):
  KIND = ReTry

  def __init__(self, schedule_key, tasks_queue):
    super(RetryDeleteMapper, self).__init__()
    self.FILTERS = [(ReTry.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue
    self.schedule_key = schedule_key
    self.count = 0

  def map_fn(self, entities):
    self.count += len(entities)
    for entity in entities:
      yield entity.key.delete_async()

  def enqueue(self, next_cursor):
    # new_mapper = RetryDeleteMapper(self.schedule_key, self.tasks_queue)
    # tasks.addTask(self.tasks_queue, new_mapper._continue)
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  @ndb.transactional(retries=2)
  def finish(self, more):
    schedule = self.schedule_key.get()
    if more:
      logging.info('ReTry has been deleted (%d) not done. \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)

    else:
      schedule.delete_mark_ReTry = True
      schedule.put()

      logging.info('ReTry delete done (%d). \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)


class LogEmailDeleteMapper(AsyncMapper):
  KIND = LogEmail

  def __init__(self, schedule_key, tasks_queue):
    super(LogEmailDeleteMapper, self).__init__()
    self.FILTERS = [(LogEmail.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue
    self.schedule_key = schedule_key
    self.count = 0

  def map_fn(self, entities):
    self.count += len(entities)
    for entity in entities:
      yield entity.key.delete_async()

  def enqueue(self, next_cursor):
    # new_mapper = LogEmailDeleteMapper(self.schedule_key, self.tasks_queue)
    # tasks.addTask(self.tasks_queue, new_mapper._continue)
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  @ndb.transactional(retries=2)
  def finish(self, more):
    schedule = self.schedule_key.get()
    if more:
      logging.info('LogEmail has been deleted (%d) not done. \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)

    else:
      schedule.delete_mark_logEmail = True
      schedule.put()

      logging.info('LogEmail delete done (%d). \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)


class LogFailEmailDeleteMapper(AsyncMapper):
  KIND = LogFailEmail

  def __init__(self, schedule_key, tasks_queue):
    super(LogFailEmailDeleteMapper, self).__init__()
    self.FILTERS = [(LogFailEmail.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue
    self.schedule_key = schedule_key
    self.count = 0

  def map_fn(self, entities):
    self.count += len(entities)
    for entity in entities:
      yield entity.key.delete_async()

  def enqueue(self, next_cursor):
    # new_mapper = LogFailEmailDeleteMapper(self.schedule_key, self.tasks_queue)
    # tasks.addTask(self.tasks_queue, new_mapper._continue)
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  @ndb.transactional(retries=2)
  def finish(self, more):
    schedule = self.schedule_key.get()
    if more:
      logging.info('LogFailEmail has been deleted (%d) not done. \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)

    else:
      schedule.delete_mark_LogFailEmail = True
      schedule.put()

      logging.info('LogFailEmail delete done (%d). \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)


class RecipientQueueDataDeleteMapper(AsyncMapper):
  KIND = RecipientQueueData

  def __init__(self, schedule_key, tasks_queue):
    super(RecipientQueueDataDeleteMapper, self).__init__()
    self.FILTERS = [(RecipientQueueData.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue
    self.schedule_key = schedule_key
    self.count = 0

  def map_fn(self, entities):
    self.count += len(entities)
    for entity in entities:
      yield entity.key.delete_async()

  def enqueue(self, next_cursor):
    # new_mapper = RecipientQueueDataDeleteMapper(self.schedule_key, self.tasks_queue)
    # tasks.addTask(self.tasks_queue, new_mapper._continue)
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  @ndb.transactional(retries=2)
  def finish(self, more):
    schedule = self.schedule_key.get()
    if more:
      logging.info('RecipientQueueData has been deleted (%d) not done. \nsubject: %s\ncategory: %s\nschedule: %s',
                   self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)

    else:
      schedule.delete_mark_RecipientQueueData = True
      schedule.put()

      logging.info('RecipientQueueData delete done (%d). \nsubject: %s\ncategory: %s\nschedule: %s', self.count,
                   schedule.subject, schedule.category, schedule.schedule_display)
