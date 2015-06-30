# coding: utf-8

import logging

import webapp2
from google.appengine.ext import ndb

import tasks
from handler.debug import ClearReTryHandler, ClearRecipientQueueDataHandler
from handler.parser_handler import ParseCSVHandler
from handler.mailsend_handler import ScheduleHandler
from handler.delete_handler import GCSResourcesDeleteHandler, ScheduleDeleteCheckHandler, ScheduleDeleteHandler
from handler.failmail_handler import RetryCheckHandler
from recipient_queue_data_health import RecipientQueueDataHealthCheckHandler

from handler.dumps import LogEailDumperHandler


class TasksHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the tasks module.")


routes = [
  (r'/tasks/parsecsv', ParseCSVHandler),
  (r'/tasks/schedule', ScheduleHandler),

  (r'/tasks/delete_resources', GCSResourcesDeleteHandler),
  (r'/tasks/delete_schedule', ScheduleDeleteHandler),
  (r'/tasks/check_schedule_delete', ScheduleDeleteCheckHandler),

  (r'/tasks/retry_check', RetryCheckHandler),

  (r'/tasks/recipient_queue_data_health_check', RecipientQueueDataHealthCheckHandler),

  webapp2.Route('/tasks/_cb/deferred/<module>/<name>', tasks.DeferredHandler),

  # debug only
  (r'/tasks/clear_retry', ClearReTryHandler),
  (r'/tasks/clear_recipient_queue_data', ClearRecipientQueueDataHandler),

  (r'/tasks/logemail_dump', LogEailDumperHandler),

  (r'/.*', TasksHandler)
]

router = ndb.toplevel(webapp2.WSGIApplication(routes, debug=True))
