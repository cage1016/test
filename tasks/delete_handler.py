import webapp2
import logging
import settings


class GCSResourcesDeleteHandler(webapp2.RequestHandler):
  @settings.ValidateGCSWithCredential
  def post(self):
    object_name = self.request.get('object_name')
    bucket_name = self.request.get('bucket_name')

    logging.info('delete tasks qeueu: delete gcs: %s/%s' % (bucket_name, object_name))

    req = self.gcs_service.objects().delete(bucket=bucket_name, object=object_name.encode('utf8'))
    resp = req.execute()

