__author__ = 'cage'

import logging
import pickle

from delorean import Delorean, parse
import datetime

from protorpc import remote
from application.apis.schedules_messages import *
from application.settings import cheerspoint_api
from application.models import Schedule

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.ext import ndb

from google.appengine.api.taskqueue import taskqueue
from application.utils import enqueue_task
from application.GCSSignedUrlGenerator import get_signed_url

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
    categories = request.categories
    per_page = request.per_page if request.per_page else PER_PAGE
    forward = True if p not in ['prev'] else False
    cursor = None

    resp = SchedulesListResponse()

    try:
      cursor = Cursor(urlsafe=c)
    except BadValueError, e:
      resp.msg = e.message

    query = Schedule.query_by_page(categories, cursor, forward, per_page)
    resp.next_cursor = query.get('next_cursor')
    resp.pre_cursor = query.get('pre_cursor')

    schedules = []
    for model in query.get('data'):
      d = parse(model.schedule_display.strftime('%Y-%m-%d %H:%M:%S'))
      d = d.datetime + datetime.timedelta(hours=8)

      c = parse(model.created.strftime('%Y-%m-%d %H:%M:%S'))
      c = c.datetime + datetime.timedelta(hours=8)

      # update
      if model.status != 'finished':
        if model.success_worker == model.get_tasks_executed_count() and (model.success_worker > 0 or model.fail_worker > 0):
          model.status = 'finished'
          model.put()

      schedule = SchedulesResponseMessage(
        urlsafe=model.key.urlsafe(),
        sendgrid_account=model.sendgrid_account,
        subject=model.subject,
        category=model.category,
        schedule_display=d.strftime('%Y-%m-%d %H:%M:%S'),
        hour_delta=model.hour_delta,
        hour_capacity=model.hour_capacity,
        hour_target_capacity=model.hour_target_capacity,
        hour_rate=model.hour_rate,
        txt_object_name=model.txt_object_name.split('/')[-1],
        edm_object_name=model.edm_object_name.split('/')[-1],
        replace_edm_csv_property=model.replace_edm_csv_property,
        invalid_email=model.invalid_email,
        error=model.error,
        created=c.strftime('%Y-%m-%d %H:%M:%S'),
        success_worker=model.success_worker,
        fail_worker=model.fail_worker,
        # tasks_executed_count=model.get_tasks_executed_count(),
        status=model.status,
        unsend_recipients_log=model.unsend_recipients_log,
        send_recipients_log=model.send_recipients_log,
        sender_name=model.sender_name,
        sender_email=model.sender_email,
        is_dry_run=model.is_dry_run
      )
      schedules.append(schedule)

    resp.data = schedules

    return resp

  @endpoints.method(SCHEDULES_GET_RESOURCE,
                    SchedulesResponseMessage,
                    name='get',
                    http_method='GET',
                    path='schedules/{id}')
  def get(self, request):
    self.check_authenciation()

    schedule = ndb.Key(urlsafe=request.id).get()

    if schedule:
      d = parse(schedule.schedule_display.strftime('%Y-%m-%d %H:%M:%S'))
      d = d.datetime + datetime.timedelta(hours=8)

      c = parse(schedule.created.strftime('%Y-%m-%d %H:%M:%S'))
      c = c.datetime + datetime.timedelta(hours=8)

      # update
      if schedule.status != 'finished':
        if schedule.success_worker == schedule.get_tasks_executed_count() and (schedule.success_worker > 0 or schedule.fail_worker > 0):
          schedule.status = 'finished'
          schedule.put()

      srm = SchedulesResponseMessage(
        urlsafe=schedule.key.urlsafe(),
        sendgrid_account=schedule.sendgrid_account,
        subject=schedule.subject,
        category=schedule.category,
        schedule_display=d.strftime('%Y-%m-%d %H:%M:%S'),
        hour_delta=schedule.hour_delta,
        hour_capacity=schedule.hour_capacity,
        hour_target_capacity=schedule.hour_target_capacity,
        hour_rate=schedule.hour_rate,
        txt_object_name=schedule.txt_object_name.split('/')[-1],
        edm_object_name=schedule.edm_object_name.split('/')[-1],
        replace_edm_csv_property=schedule.replace_edm_csv_property,
        invalid_email=schedule.invalid_email,
        error=schedule.error,
        created=c.strftime('%Y-%m-%d %H:%M:%S'),
        success_worker=schedule.success_worker,
        fail_worker=schedule.fail_worker,
        tasks_executed_count=schedule.get_tasks_executed_count() if schedule.status != 'finished' else schedule.success_worker,
        status=schedule.status,
        unsend_recipients_log=schedule.unsend_recipients_log,
        send_recipients_log=schedule.send_recipients_log,
        sender_name=schedule.sender_name,
        sender_email=schedule.sender_email,
        is_dry_run=schedule.is_dry_run
      )

      if schedule.send_recipients_log not in ['preparing', '']:
        srm.send_recipients_log = get_signed_url(schedule.send_recipients_log)

      if schedule.unsend_recipients_log not in ['preparing', '']:
        srm.unsend_recipients_log = get_signed_url(schedule.unsend_recipients_log)

      return srm

    else:
      return SchedulesResponseMessage()

  @endpoints.method(SCHEDULES_INSERT_RESOURCE,
                    SchedulesInsertResponse,
                    name='insert',
                    http_method='POST',
                    path='schedules')
  def insert(self, request):
    self.check_authenciation()

    logging.info('assign parse job')

    recipient_txt = ndb.Key(urlsafe=request.recipientTxtUrlsafe).get()
    recipient_edm = ndb.Key(urlsafe=request.recipientEdmUrlsafe).get()

    parameters = {
      'subject': request.subject,
      'sender_name': request.senderName,
      'sender_email': request.senderEmail,
      'type': request.type,
      'txt_object_name': recipient_txt.object_name,
      'edm_object_name': recipient_edm.object_name,
      'bucket_name': recipient_txt.bucket,
      'schedule_duration': request.scheduleDuration,
      'ip_counts': request.ipCounts,
      'daily_capacity': request.dailyCapacity,
      'category': request.category.encode('utf8'),
      'reply_to': request.replyTo.encode('utf8'),
      'recipient_skip': request.recipientSkip,
      'start_time': request.startTime.encode('utf8'),
      'hour_rate': request.hourRate,
      'sendgrid_account': request.sendgridAccount,
      'replace_edm_csv_property': request.replaceEdmCSVProperty
    }

    logging.info(parameters)

    r = enqueue_task(url='/tasks/parsecsv',
                     queue_name='parsecsv',
                     params={
                       'parameters': pickle.dumps(parameters)
                     })

    return SchedulesInsertResponse(msg=str(r))

  @endpoints.method(SCHEDULES_DELETE_RESOURCE,
                    SchedulesResponseMessage,
                    name='delete',
                    http_method='DELETE',
                    path='schedules/{id}')
  def delete(self, request):
    self.check_authenciation()

    schedule = ndb.Key(urlsafe=request.id).get()
    if schedule:

      try:
        schedule.status = 'deleting'
        schedule.put()

        taskqueue.add(url='/tasks/delete_schedule',
                      params={
                        'urlsafe': request.id
                      },
                      queue_name='resource-delete')



      except taskqueue.Error, error:
        logging.error('An error occurred in endpoints APIs: %s' % error)

      d = parse(schedule.schedule_display.strftime('%Y-%m-%d %H:%M:%S'))
      d = d.datetime + datetime.timedelta(hours=8)

      c = parse(schedule.created.strftime('%Y-%m-%d %H:%M:%S'))
      c = c.datetime + datetime.timedelta(hours=8)

      srm = SchedulesResponseMessage(
        urlsafe=schedule.key.urlsafe(),
        sendgrid_account=schedule.sendgrid_account,
        subject=schedule.subject,
        category=schedule.category,
        schedule_display=d.strftime('%Y-%m-%d %H:%M:%S'),
        hour_delta=schedule.hour_delta,
        hour_capacity=schedule.hour_capacity,
        hour_target_capacity=schedule.hour_target_capacity,
        hour_rate=schedule.hour_rate,
        txt_object_name=schedule.txt_object_name.split('/')[-1],
        edm_object_name=schedule.edm_object_name.split('/')[-1],
        replace_edm_csv_property=schedule.replace_edm_csv_property,
        invalid_email=schedule.invalid_email,
        error=schedule.error,
        created=c.strftime('%Y-%m-%d %H:%M:%S'),
        success_worker=schedule.success_worker,
        fail_worker=schedule.fail_worker,
        tasks_executed_count=schedule.get_tasks_executed_count(),
        status=schedule.status,
        unsend_recipients_log=schedule.unsend_recipients_log,
        send_recipients_log=schedule.send_recipients_log,
        is_dry_run=schedule.is_dry_run
      )
      return srm

    else:
      return SchedulesResponseMessage()

  @endpoints.method(SCHEDULES_DUMP_RESOURCE,
                    SchedulesResponseMessage,
                    name='dump',
                    http_method='POST',
                    path='schedule/dump/{id}')
  def dump(self, request):
    self.check_authenciation()

    schedule = ndb.Key(urlsafe=request.id).get()

    if schedule:
      r = enqueue_task(url='/tasks/dump',
                       queue_name='fire-dump',
                       params={
                         'urlsafe': request.id,
                         'dump_type': request.dumpType
                       })

      if request.dumpType == 'send':
        if r:
          schedule.send_recipients_log = 'preparing'

        else:
          schedule.send_recipients_log = 'can not add job, try it later'

        schedule.put()

      elif request.dumpType == 'unsend':
        if r:
          schedule.unsend_recipients_log = 'preparing'

        else:
          schedule.send_recipients_log = 'can not add job, try it later'

        schedule.put()

      d = parse(schedule.schedule_display.strftime('%Y-%m-%d %H:%M:%S'))
      d = d.datetime + datetime.timedelta(hours=8)

      c = parse(schedule.created.strftime('%Y-%m-%d %H:%M:%S'))
      c = c.datetime + datetime.timedelta(hours=8)

      return SchedulesResponseMessage(
        urlsafe=schedule.key.urlsafe(),
        sendgrid_account=schedule.sendgrid_account,
        subject=schedule.subject,
        category=schedule.category,
        schedule_display=d.strftime('%Y-%m-%d %H:%M:%S'),
        hour_delta=schedule.hour_delta,
        hour_capacity=schedule.hour_capacity,
        hour_target_capacity=schedule.hour_target_capacity,
        hour_rate=schedule.hour_rate,
        txt_object_name=schedule.txt_object_name.split('/')[-1],
        edm_object_name=schedule.edm_object_name.split('/')[-1],
        replace_edm_csv_property=schedule.replace_edm_csv_property,
        invalid_email=schedule.invalid_email,
        error=schedule.error,
        created=c.strftime('%Y-%m-%d %H:%M:%S'),
        success_worker=schedule.success_worker,
        fail_worker=schedule.fail_worker,
        tasks_executed_count=schedule.get_tasks_executed_count(),
        status=schedule.status,
        unsend_recipients_log=schedule.unsend_recipients_log,
        send_recipients_log=schedule.send_recipients_log,
        sender_name=schedule.sender_name,
        sender_email=schedule.sender_email,
        is_dry_run=schedule.is_dry_run
      )

    return SchedulesResponseMessage()
