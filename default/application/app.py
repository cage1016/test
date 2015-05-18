#!/usr/bin/env python
# -*- coding:utf-8 -*-

import webapp2

from application.controllers.basehandler import BaseHandler
from application.controllers.recipients_handler import RecipientsManageHandler
from application.controllers.sendmail_handler import SendMailHandler
from application.controllers.template_handler import TemplateManageHandler
from application.controllers.reports_handler import reports_routes

from application.controllers.test_handler import TestAccountHandler
from application.controllers.poc_handler import POCHandler

from application import blob_serve
from application.controllers.error_handler import Handle403, Handle404, Handle500


class MainHandler(BaseHandler):
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
    ('/test_account', TestAccountHandler),
    ('/poc_account', POCHandler),
    ('/sendmail', SendMailHandler),
    ('/template', TemplateManageHandler),
    ('/recipients', RecipientsManageHandler),
    ('/tasks/schedule', 'application.tasks.schedule_handler.ScheduleHandler'),
    ('/tasks/mailer', 'application.tasks.mailer_handler.MailerHandler'),
    ('/tasks/worker', 'application.tasks.worker_handler.WorkHandler'),
    ('/tasks/delete/recipeints', 'application.tasks.delete_handler.RecipientDeleteHandler'),
    ('/tasks/delete/recipeint_queue', 'application.tasks.delete_handler.RecipientQueueDataDeleteHandler'),
    ('/use_blobstore/([^/]+)?', blob_serve.UseBlobstore)
]

# add reports routes
routes.extend(reports_routes)

router = webapp2.WSGIApplication(routes, debug=True)

router.error_handlers[404] = Webapp2HandlerAdapter(Handle404)
router.error_handlers[403] = Webapp2HandlerAdapter(Handle403)
router.error_handlers[500] = Webapp2HandlerAdapter(Handle500)