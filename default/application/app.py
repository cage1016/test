#!/usr/bin/env python
# -*- coding:utf-8 -*-

import webapp2
import endpoints
from application.apis import recipients

from application.controllers.base import *
from application.controllers.recipients_handler import RecipientsManageHandler
from application.controllers.sendmail_handler import SendMailHandler
from application.controllers.template_handler import TemplateManageHandler
from application.controllers.reports_handler import reports_routes
from application.controllers.account_handler import account_management_route
from application.controllers.ipwarmup_handler import ip_warmup_route

from application import blob_serve
from application.controllers.error_handler import Handle403, Handle404, Handle500

# from settings import decorator
from secrets import SESSION_KEY

# webapp2 config
app_config = {
  'webapp2_extras.sessions': {
    'secret_key': SESSION_KEY
  },
  'webapp2_extras.auth': {
    'user_model': User
  }
}


class MainHandler(BaseRequestHandler):
  def get(self):
    self.render('index.html')


class Webapp2HandlerAdapter(webapp2.BaseHandlerAdapter):
  def __call__(self, request, response, exception):
    request.route_args = {}
    request.route_args['exception'] = exception
    handler = self.handler(request, response)

    return handler.get()


routes = [
  ('/', MainHandler),

  ('/oauth2callback', OAuth2CallbackHandler),
  ('/logout', LogOutHandler),

  ('/sendmail', SendMailHandler),
  ('/template', TemplateManageHandler),
  ('/recipients', RecipientsManageHandler),

  ('/tasks/schedule', 'application.tasks.schedule_handler.ScheduleHandler'),
  ('/tasks/mailer', 'application.tasks.mailer_handler.MailerHandler'),
  ('/tasks/worker', 'application.tasks.worker_handler.WorkHandler'),

  ('/tasks/delete/recipeints', 'application.tasks.delete_handler.RecipientDeleteHandler'),
  ('/tasks/delete/recipeint_queue', 'application.tasks.delete_handler.RecipientQueueDataDeleteHandler'),
  ('/tasks/delete/recipeint_txt_queue', 'application.tasks.delete_handler.RecipientTxtDeleteHandler'),

  ('/use_blobstore/([^/]+)?', blob_serve.UseBlobstore)
]

# add reports routes
routes.extend(reports_routes)
routes.extend(account_management_route)
routes.extend(ip_warmup_route)

router = webapp2.WSGIApplication(routes, config=app_config, debug=True)

# router.error_handlers[404] = Webapp2HandlerAdapter(Handle404)
router.error_handlers[403] = Webapp2HandlerAdapter(Handle403)
# router.error_handlers[500] = Webapp2HandlerAdapter(Handle500)

API = endpoints.api_server([
  recipients.RecipientApi
])