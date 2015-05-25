__author__ = 'cage'

import logging
import json

from protorpc import remote
from application.controllers.base import ValidateGCSWithCredential
from application.apis.resources_messages import *
from application.settings import cheerspoint_api
from application.models import Resource

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.ext import ndb
from apiclient.http import MediaInMemoryUpload
from apiclient import errors

from google.appengine.api.taskqueue import taskqueue

import application.settings as settings

raise_unauthorized = True

PER_PAGE = 20


@cheerspoint_api.api_class(resource_name='resources')
class ResourceApi(remote.Service):
  def query(self, recipient_txt, cursor, forward, per_page, **params):

    if forward:
      recipient_txt, next_cursor, more = recipient_txt.order(-Resource.created).fetch_page(per_page,
                                                                                               start_cursor=cursor)

      if next_cursor and more:
        next_cursor = next_cursor.urlsafe()
        params.update(next_cursor=next_cursor)

      if cursor:
        pre_cursor = cursor.reversed().urlsafe()
        params.update(pre_cursor=pre_cursor)

    else:
      recipient_txt, next_cursor, more = recipient_txt.order(Resource.created).fetch_page(per_page,
                                                                                              start_cursor=cursor)

      if next_cursor and more:
        pre_cursor = next_cursor.urlsafe()
        params.update(pre_cursor=pre_cursor)

      next_cursor = cursor.reversed().urlsafe()
      params.update(next_cursor=next_cursor)

    params.update(resources=[w.to_response_message() for w in recipient_txt])

    return params

  def check_authenciation(self):
    current_user = endpoints.get_current_user()
    if raise_unauthorized and current_user is None:
      raise endpoints.UnauthorizedException('Invalid token.')

  @endpoints.method(RESOURCES_LIST_RESOURCE,
                    ResourcesListResponse,
                    name='list',
                    http_method='GET',
                    path='resources')
  def list(self, request):
    self.check_authenciation()

    p = request.p
    c = request.c
    per_page = request.per_page if request.per_page else PER_PAGE
    forward = True if p not in ['prev'] else False
    cursor = None

    resp = ResourcesListResponse()

    try:
      cursor = Cursor(urlsafe=c)
    except BadValueError, e:
      resp.msg = e.message

    query = self.query(Resource.query(), cursor, forward, per_page)
    resp.resources = query.get('resources')
    resp.next_cursor = query.get('next_cursor')
    resp.pre_cursor = query.get('pre_cursor')

    return resp


  @endpoints.method(RESOURCES_INSERT_RESOURCE,
                    ResourcesResponseMessage,
                    name='insert',
                    http_method='POST',
                    path='resources')
  def insert(self, request):
    self.check_authenciation()

    id = '/'.join(request.id.split('/')[:-1])
    recipient_text = Resource.get_or_insert(id)
    recipient_text.object_name = request.name
    recipient_text.display_name = request.name.split('/')[-1]
    recipient_text.bucket = request.bucket
    recipient_text.size = int(request.size)
    recipient_text.content_type = request.contentType
    recipient_text.put()

    return recipient_text.to_response_message()

  @endpoints.method(RESOURCES_DELETE_RESOURCE,
                    ResourcesDeleteResponse,
                    name='delete',
                    http_method='DELETE',
                    path='resources/{id}')
  def delete(self, request):
    self.check_authenciation()

    recipient_txt = ndb.Key(urlsafe=request.id).get()
    if recipient_txt:

      try:
        recipient_txt.key.delete()

        if not settings.DEBUG:
          taskqueue.add(url='/tasks/delete_resources',
                        params={
                          'object_name': recipient_txt.object_name,
                          'bucket_name': recipient_txt.bucket
                        },
                        queue_name='resource-delete')

        else:
          logging.info(
            '_ah/spi is not a dispatchable path, task queue:delete_resources won\'t be executed at development env. ')

      except taskqueue.Error, error:
        logging.error('An error occurred in endpoints APIs: %s' % error)

    return ResourcesDeleteResponse(urlsafe=request.id)