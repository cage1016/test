#!/usr/bin/env python
# -*- coding:utf-8 -*-

import webapp2
import endpoints
from application.apis import resources

from application.controllers.base import *

from application.controllers.mail_handler import SendMailHandler

from application.controllers.reports_handler import reports_routes
from application.controllers.account_handler import account_management_route
from application.controllers.ipwarmup_handler import ip_warmup_route


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
  ('/me', MeHandler),

  ('/mail', SendMailHandler)
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
  resources.ResourceApi
])