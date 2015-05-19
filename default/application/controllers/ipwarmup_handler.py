__author__ = 'cage'

import json
from application.controllers.base import *

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext.db import Error, BadValueError
from google.appengine.api.taskqueue import taskqueue

from application.models import RecipientTxt


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


class IPWamrupRecipientHandler(BaseRequestHandler):
  @my_login_required
  @my_admin_required
  def get(self):
    params = {}

    self.render('ipwarmup/ipwarmup_recipient.html', **params)


class IPWamrupInsertHandler(AbstractHandler):
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

    params.update(recipient=[w.to_dict() for w in recipient_txt])

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


class IPWamrupDeleteHandler(AbstractHandler):
  def post(self):
    urlsafe = self.request.get('urlsafe')

    recipient_txt = ndb.Key(urlsafe=urlsafe).get()
    if recipient_txt:
      taskqueue.add(url='/tasks/delete/recipeint_txt_queue',
                    params={'object_name': recipient_txt.object_name},
                    queue_name='recipient-queue-delete')

      recipient_txt.key.delete()

    self.render_response('ok')


ip_warmup_route = [
  (r'/ipwarmup', IPWamrupListHandler),
  # (r'/ipwarmup/new', IPWamrupNewHandler),
  (r'/ipwarmup/recipient', IPWamrupRecipientHandler),


  (r'/api/recipient', RecipientsListHandler),
  (r'/api/recipient/insert', IPWamrupInsertHandler),
  (r'/api/recipient/delete', IPWamrupDeleteHandler),
  (r'/api/me', MeHandler),
]