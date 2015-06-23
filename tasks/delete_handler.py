import webapp2
import logging
import settings
import httplib2

from google.appengine.ext import ndb
from models import RecipientQueueData, ReTry, Schedule, LogEmail, LogFailEmail
from apiclient.errors import HttpError

from datastore_utils import Mapper
import tasks

from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials


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
    done_RecipientQueueData = True if not RecipientQueueData.query(
      RecipientQueueData.schedule_key == schedule.key).get() else False
    done_logEmail = True if not LogFailEmail.query(LogFailEmail.schedule_key == schedule.key).get() else False
    done_FailLogEmail = True if not LogFailEmail.query(LogFailEmail.schedule_key == schedule.key).get() else False
    done_Retry = True if not ReTry.query(ReTry.schedule_key == schedule.key).get() else False

    if done_RecipientQueueData and done_logEmail and done_FailLogEmail and done_Retry:
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

      mapper_RecipientQueueData = RecipientQueueDataMapper(schedule.key, ['schedule-delete-mapper'])
      mapper_logEmail = LogEmailMapper(schedule.key, ['schedule-delete-mapper'])
      mapper_FailLogEmail = LogFailEmailMapper(schedule.key, ['schedule-delete-mapper'])
      mapper_Retry = RetryMapper(schedule.key, ['schedule-delete-mapper'])

      tasks.addTask(['schedule-delete-mapper'], mapper_RecipientQueueData.run)
      tasks.addTask(['schedule-delete-mapper'], mapper_logEmail.run)
      tasks.addTask(['schedule-delete-mapper'], mapper_FailLogEmail.run)
      tasks.addTask(['schedule-delete-mapper'], mapper_Retry.run)


class RetryMapper(Mapper):
  KIND = ReTry

  def __init__(self, schedule_key, tasks_queue):
    super(RetryMapper, self).__init__()
    self.FILTERS = [(ReTry.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

  def map(self, entity):
    return ([], [entity.key])


class LogEmailMapper(Mapper):
  KIND = LogEmail

  def __init__(self, schedule_key, tasks_queue):
    super(LogEmailMapper, self).__init__()
    self.FILTERS = [(LogEmail.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

  def map(self, entity):
    return ([], [entity.key])


class LogFailEmailMapper(Mapper):
  KIND = LogFailEmail

  def __init__(self, schedule_key, tasks_queue):
    super(LogFailEmailMapper, self).__init__()
    self.FILTERS = [(LogFailEmail.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

  def map(self, entity):
    return ([], [entity.key])


class RecipientQueueDataMapper(Mapper):
  KIND = RecipientQueueData

  def __init__(self, schedule_key, tasks_queue):
    super(RecipientQueueDataMapper, self).__init__()
    self.FILTERS = [(RecipientQueueData.schedule_key, schedule_key)]
    self.tasks_queue = tasks_queue

  def map(self, entity):
    return ([], [entity.key])
