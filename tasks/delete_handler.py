from apiclient.errors import HttpError
import webapp2
import logging
import settings

from google.appengine.ext import ndb
from models import RecipientQueueData

from datastore_utils import page_queries
from utils import timeit, enqueue_task
import time


class GCSResourcesDeleteHandler(webapp2.RequestHandler):
  @settings.ValidateGCSWithCredential
  def post(self):
    object_name = self.request.get('object_name')
    bucket_name = self.request.get('bucket_name')

    logging.info('delete tasks qeueu: delete gcs: %s/%s' % (bucket_name, object_name))

    try:

      req = self.gcs_service.objects().delete(bucket=bucket_name, object=object_name.encode('utf8'))
      resp = req.execute()

    except HttpError, error:
      logging.info(error)


class ScheduleDeleteHandler(webapp2.RequestHandler):
  @ndb.toplevel
  @timeit
  def post(self):
    schedule_urlsafe = self.request.get('urlsafe')
    count = int(self.request.get('count')) if self.request.get('count') else 0

    schedule = ndb.Key(urlsafe=schedule_urlsafe).get()

    if schedule:
      ancestor_key = schedule.key

      queries = [
        RecipientQueueData.query(ancestor=ancestor_key)
      ]

      for keys in page_queries(queries, fetch_page_size=100):
        count += len(keys)
        yield ndb.delete_multi_async(keys=keys)

        if (time.time() - self.ts).__int__() > settings.MAX_TASKSQUEUE_EXECUTED_TIME:
          enqueue_task(url='/tasks/dt',
                       queue_name='delete-test',
                       params={
                         'urlsafe': schedule_urlsafe,
                         'count': count
                       })
          break

      logging.info('delete %s - RecipientQueueData(%d/%d) finished.' % (schedule.subject,
                                                                        count * settings.RECIPIENT_CHENKS_SIZE,
                                                                        schedule.hour_capacity))

      if count * settings.RECIPIENT_CHENKS_SIZE == schedule.hour_capacity:
        schedule.key.delete()
        logging.info('delete %s finished.' % schedule.subject)

      if count == 0 or (count == 1 and (schedule.hour_capacity <= count * settings.RECIPIENT_CHENKS_SIZE)):
        schedule.key.delete()
        logging.info('delete %s finished.' % schedule.subject)
