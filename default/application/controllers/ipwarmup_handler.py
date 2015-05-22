from apiclient.http import MediaIoBaseDownload
from application.utils import ipwarmup_day_sending_rate

__author__ = 'cage'

import json
from application.controllers.base import *
from google.appengine.ext import ndb

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.api.taskqueue import taskqueue

from application.models import RecipientTxt, Schedule

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


class IPWamrupRecipientHandler(BaseRequestHandler):
  @my_login_required
  @my_admin_required
  def get(self):
    params = {}

    self.render('ipwarmup/ipwarmup_recipient.html', **params)


class RecipientsInsertHandler(AbstractHandler):
  def post(self):
    data = self.request.get('data')

    if data:
      data = json.loads(data)
      id = '/'.join(data.get('id').split('/')[:-1])
      recipient_text = RecipientTxt.get_or_insert(id)
      recipient_text.object_name = data.get('name')
      recipient_text.display_name = data.get('name').split('/')[1]
      recipient_text.bucket = data.get('bucket')
      recipient_text.size = int(data.get('size'))
      recipient_text.content_type = data.get('contentType')
      recipient_text.put()

    self.render_response(data)


class RecipientsListHandler(AbstractHandler):
  def query(self, recipient_txt, cursor, forward, per_page, **params):

    if forward:
      recipient_txt, next_cursor, more = recipient_txt.order(-RecipientTxt.created).fetch_page(per_page,
                                                                                               start_cursor=cursor)

      if next_cursor and more:
        next_cursor = next_cursor.urlsafe()
        params.update(next_cursor=next_cursor)

      if cursor:
        pre_cursor = cursor.reversed().urlsafe()
        params.update(pre_cursor=pre_cursor)

    else:
      recipient_txt, next_cursor, more = recipient_txt.order(RecipientTxt.created).fetch_page(per_page,
                                                                                              start_cursor=cursor)

      if next_cursor and more:
        pre_cursor = next_cursor.urlsafe()
        params.update(pre_cursor=pre_cursor)

      next_cursor = cursor.reversed().urlsafe()
      params.update(next_cursor=next_cursor)

    params.update(recipient=[w._to_dict() for w in recipient_txt])

    return params

  @my_login_required
  @my_admin_required
  def get(self):

    c = self.request.get('c')
    p = self.request.get('p')
    per_page = self.request.get('per_page ') if self.request.get('per_page ')  else 10
    forward = True if p not in ['prev'] else False
    cursor = None

    try:
      cursor = Cursor(urlsafe=c)
    except BadValueError, e:
      pass

    query = self.query(RecipientTxt.query(), cursor, forward, per_page)

    self.render_response(query)


class MeHandler(AbstractHandler):
  @my_login_required
  @my_admin_required
  @ValidateCheerspointServiceWithCredential
  def get(self):
    credential = pickle.loads(self.session.get('credential'))
    self.render_response(credential.access_token)


class RecipientsDeleteHandler(AbstractHandler):
  def post(self):
    urlsafe = self.request.get('urlsafe')

    recipient_txt = ndb.Key(urlsafe=urlsafe).get()
    if recipient_txt:
      taskqueue.add(url='/tasks/delete/recipeint_txt_queue',
                    params={'object_name': recipient_txt.object_name},
                    queue_name='recipient-queue-delete')

      recipient_txt.key.delete()

    self.render_response('ok')


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


class IPWamrupJobListHandler(AbstractHandler):
  def get(self):
    ip_warmup_schedule = Schedule.query().order(Schedule.created).fetch()

    self.render_response([x._to_dict() for x in ip_warmup_schedule])


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
  (r'/ipwarmup/recipient', IPWamrupRecipientHandler),

  (r'/api/ipwarmup/addjob', IPWamrupAddJobHandler),
  (r'/api/ipwarmup/joblist', IPWamrupJobListHandler),

  (r'/api/recipient', RecipientsListHandler),
  (r'/api/recipient/insert', RecipientsInsertHandler),
  (r'/api/recipient/delete', RecipientsDeleteHandler),
  (r'/api/me', MeHandler),

  (r'/api/dump', DumpHandler)
]