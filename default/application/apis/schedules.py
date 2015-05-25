__author__ = 'cage'

import logging
import json

from protorpc import remote
from application.controllers.base import ValidateGCSWithCredential
from application.apis.schedules_messages import *
from application.settings import cheerspoint_api
from application.models import Schedule

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.ext import ndb
from apiclient.http import MediaInMemoryUpload
from apiclient import errors

from google.appengine.api.taskqueue import taskqueue

import application.settings as settings

raise_unauthorized = True

PER_PAGE = 20


@cheerspoint_api.api_class(resource_name='schedules')
class ScheduleApi(remote.Service):
  def check_authenciation(self):
    current_user = endpoints.get_current_user()
    if raise_unauthorized and current_user is None:
      raise endpoints.UnauthorizedException('Invalid token.')

  @endpoints.method(SCHEDULES_LIST_RESOURCE,
                    SchedulesListResponse,
                    name='list',
                    http_method='GET',
                    path='schedules')
  def list(self, request):
    self.check_authenciation()

    p = request.p
    c = request.c
    per_page = request.per_page if request.per_page else PER_PAGE
    forward = True if p not in ['prev'] else False
    cursor = None

    resp = SchedulesListResponse()

    try:
      cursor = Cursor(urlsafe=c)
    except BadValueError, e:
      resp.msg = e.message

    query = Schedule.query_by_page(cursor, forward, per_page)
    resp.next_cursor = query.get('next_cursor')
    resp.pre_cursor = query.get('pre_cursor')

    schedules = []
    for model in query.get('data'):
      schedule = SchedulesResponseMessage(
        urlsafe=model.key.urlsafe(),
        subject=model.subject,
        category=model.category,
        schedule_display=model.schedule_display.strftime('%Y-%m-%d %H:%M:%S'),
        hour_delta=model.hour_delta,
        hour_capacity=model.hour_capacity,
        hour_rate=model.hour_rate,
        txt_object_name=model.txt_object_name,
        edm_object_name=model.edm_object_name,
        created=model.created.strftime('%Y-%m-%d %H:%M:%S')
      )
      schedules.append(schedule)

    resp.data = schedules

    return resp
