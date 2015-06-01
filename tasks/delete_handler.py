from apiclient.errors import HttpError
import webapp2
import logging
import settings

from google.appengine.ext import ndb
from models import RecipientQueueData


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
  def post(self):
    schedule_urlsafe = self.request.get('urlsafe')
    schedule = ndb.Key(urlsafe=schedule_urlsafe).get()

    if schedule:
      ancestor_key = schedule.key

      logging.info('schedule ancestor_key_urlsafe:%s' % schedule_urlsafe)
      yield RecipientQueueData.delete_all_for_schedule(ancestor_key)

      schedule.key.delete()