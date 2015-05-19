__author__ = 'cage'

import logging
import json

from protorpc import remote
from application.controllers.base import ValidateGCSWithCredential
from application.apis.recipients_messages import *
from application.settings import cheerspoint_api

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.ext import ndb
from apiclient.http import MediaInMemoryUpload
from apiclient import errors

raise_unauthorized = True


@cheerspoint_api.api_class(resource_name='recipients')
class RecipientApi(remote.Service):
  def check_authenciation(self):
    current_user = endpoints.get_current_user()
    if raise_unauthorized and current_user is None:
      raise endpoints.UnauthorizedException('Invalid token.')

  @endpoints.method(RECIPIENT_INSERT_RESOURCE,
                    RecipientInsertResponse,
                    name='insert',
                    http_method='POST',
                    path='recipients/insert')
  @ValidateGCSWithCredential
  def insert(self, request):

    self.check_authenciation()

    email = endpoints.get_current_user().email()
    media = MediaInMemoryUpload(request.body, mimetype=request.content_type)

    try:

      req = self.gcs_service.objects().insert(
        bucket=self.gcs_service.BUCKET,
        name='{email}/{file_name}'.format(email=email, file_name=request.file_name).encode('utf8'),
        media_body=media
      )
      resp = req.execute()

    except errors as e:
      logging.error('waldo.waypoints.insert error : {message}'.format(message=e.message))
      raise endpoints.BadRequestException(messages=e.message)

    logging.debug(json.dumps(resp))

    # ancestor_key = ndb.Key('User', email)
    # waypoint = Waypoints(parent=ancestor_key, id=resp.get('id'))
    # waypoint.object_name = resp.get('name')
    # waypoint.put()
    #
    rir = RecipientInsertResponse()
    rir.id = resp.get('id')
    rir.name = resp.get('name')
    rir.bucket = resp.get('bucket')

    return rir