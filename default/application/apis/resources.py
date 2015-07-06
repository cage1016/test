__author__ = 'cage'

import logging
from delorean import parse
import datetime

from protorpc import remote

from application.apis.resources_messages import *
from application.settings import cheerspoint_api
from application.models import Resource

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import BadValueError
from google.appengine.ext import ndb
from google.appengine.api.taskqueue import taskqueue

import application.settings as settings

raise_unauthorized = True

PER_PAGE = 20


@cheerspoint_api.api_class(resource_name='resources')
class ResourceApi(remote.Service):
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

    query = Resource.query_by_page(cursor, forward, per_page)
    resp.next_cursor = query.get('next_cursor')
    resp.pre_cursor = query.get('pre_cursor')

    resources = []
    for model in query.get('data'):
      d = parse(model.created.strftime('%Y-%m-%d %H:%M:%S'))
      d = d.datetime + datetime.timedelta(hours=8)

      resource = ResourcesResponseMessage(
        object_name=model.object_name,
        display_name=model.display_name,
        bucket=model.bucket,
        size=model.size,
        content_type=model.content_type,
        created=d.strftime('%Y-%m-%d %H:%M:%S'),
        urlsafe=model.key.urlsafe()
      )
      resources.append(resource)

    resp.data = resources

    return resp


  @endpoints.method(RESOURCES_INSERT_RESOURCE,
                    ResourcesResponseMessage,
                    name='insert',
                    http_method='POST',
                    path='resources')
  def insert(self, request):
    self.check_authenciation()

    id = '/'.join(request.id.split('/')[:-1])
    resource = Resource.get_or_insert(id)
    resource.object_name = request.name
    resource.display_name = request.name.split('/')[-1]
    resource.bucket = request.bucket
    resource.size = int(request.size)
    resource.content_type = request.contentType
    resource.put()

    return ResourcesResponseMessage(
      object_name=resource.object_name,
      display_name=resource.display_name,
      bucket=resource.bucket,
      size=resource.size,
      content_type=resource.content_type,
      created=resource.created.strftime('%Y-%m-%d %H:%M:%S'),
      urlsafe=resource.key.urlsafe()
    )

  @endpoints.method(RESOURCES_DELETE_RESOURCE,
                    ResourcesDeleteResponse,
                    name='delete',
                    http_method='DELETE',
                    path='resources/{id}')
  def delete(self, request):
    self.check_authenciation()

    resource = ndb.Key(urlsafe=request.id).get()
    if resource:

      try:
        resource.key.delete()

        if not settings.DEBUG:
          taskqueue.add(url='/tasks/delete_resources',
                        params={
                          'object_name': resource.object_name,
                          'bucket_name': resource.bucket
                        },
                        queue_name='resource-delete')

        else:
          logging.info(
            '/_ah/spi is not a dispatchable path, task queue:delete_resources won\'t be executed at development env. ')

      except taskqueue.Error, error:
        logging.error('An error occurred in endpoints APIs: %s' % error)

    return ResourcesDeleteResponse(urlsafe=request.id)