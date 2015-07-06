from apiclient.http import MediaIoBaseDownload
from application.utils import ipwarmup_day_sending_rate

__author__ = 'cage'

import json
from application.controllers.base import *
from google.appengine.ext import ndb

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.api.taskqueue import taskqueue

from application.models import Resource, Schedule

from apiclient.errors import HttpError
import time
import random
import csv
import io

CHUNKSIZE = 2 * 1024 * 1024


class AbstractHandler(BaseRequestHandler):
  def render_response(self, response):
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(response))


class IPWamrupListHandler(BaseRequestHandler):
  @my_login_required
  @my_admin_required
  def get(self):
    params = {}

    self.render('ipwarmup/ipwarmup_list.html', **params)


class IPWamrupNewHandler(BaseRequestHandler):
  @my_login_required
  @my_admin_required
  def get(self):
    params = {}

    self.render('ipwarmup/ipwarmup_new.html', **params)


class IPWamrupResourceHandler(BaseRequestHandler):
  @my_login_required
  @my_admin_required
  def get(self):
    params = {}

    self.render('ipwarmup/ipwarmup_resource.html', **params)


class IPWamrupScheduleDetailHandler(BaseRequestHandler):
  @my_login_required
  @my_admin_required
  def get(self, id):
    self.render('ipwarmup/ipwarmup_detail.html')


class IPWamrupAddJobHandler(AbstractHandler):
  def post(self):
    recipient_txt_urlsafe = self.request.get('recipientTxtUrlsafe')
    recipient_edm_urlsafe = self.request.get('recipientEdmUrlsafe')
    recipient_txt = ndb.Key(urlsafe=recipient_txt_urlsafe).get()
    recipient_edm = ndb.Key(urlsafe=recipient_edm_urlsafe).get()

    parameters = {
      'subject': self.request.get('subject'),
      'sender_name': self.request.get('senderName'),
      'sender_email': self.request.get('senderEmail'),
      'type': self.request.get('type'),
      'txt_object_name': recipient_txt.object_name,
      'edm_object_name': recipient_edm.object_name,
      'bucket_name': recipient_txt.bucket,
      'schedule_duration': self.request.get('scheduleDuration'),
      'ip_counts': self.request.get('ipCounts'),
      'daily_capacity': self.request.get('dailyCapacity'),
      'category': self.request.get('category').encode('utf8'),
      'recipient_skip': self.request.get('recipientSkip'),
      'start_time': self.request.get('startTime').encode('utf8'),
      'hour_rate': self.request.get('hourRate'),
    }

    logging.info('assign parse job')
    # time.sleep(2)
    taskqueue.add(url='/tasks/parsecsv',
                  params={
                    'parameters': pickle.dumps(parameters)
                  },
                  queue_name='parsecsv')

    self.render_response('ok')


class DumpHandler(AbstractHandler):
  def get(self):

    result = {}

    ip_warmups = Schedule.query().order(Schedule.schedule_timestamp).fetch()

    for ip in ip_warmups:
      name = ip.schedule_display.strftime('%Y/%m/%d %H:%M')
      result[name] = []

      for queue in ndb.get_multi(ip.recipientQueue):
        result[name].append(
          json.loads(queue.data)
        )

    self.render_response(result)


ip_warmup_route = [
  (r'/ipwarmup', IPWamrupListHandler),
  (r'/ipwarmup/new', IPWamrupNewHandler),
  (r'/ipwarmup/resource', IPWamrupResourceHandler),
  (r'/ipwarmup/detail/(\S+)', IPWamrupScheduleDetailHandler),

  (r'/api/ipwarmup/addjob', IPWamrupAddJobHandler),

  (r'/api/dump', DumpHandler)
]