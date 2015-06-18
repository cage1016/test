import webapp2
import logging
from parser_handler import ParseCSVHandler
from mailsend_handler import *
from delete_handler import *
from failmail_handler import *

import tasks


class TasksHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the tasks module.")


routes = [
  (r'/tasks/parsecsv', ParseCSVHandler),

  (r'/tasks/schedule', ScheduleHandler),
  # (r'/tasks/mailer', MailerHandler),
  # (r'/tasks/worker', WorkHandler),
  # (r'/tasks/worker2', WorkHandler),

  # (r'/tasks/success_log_save', SuccessLogSaveHandler),
  # (r'/tasks/fail_log_save', FailLogSaveHandler),

  (r'/tasks/delete_resources', GCSResourcesDeleteHandler),
  (r'/tasks/delete_schedule', ScheduleDeleteHandler),

  (r'/tasks/retry_check', RetryCheckHandler),
  (r'/tasks/retry_resend', RetrySendWorkHandler),
  # (r'/tasks/retry_delete', RetryDelete),

  webapp2.Route('/tasks/_cb/deferred/<module>/<name>', tasks.DeferredHandler),

  (r'/.*', TasksHandler)
]

router = ndb.toplevel(webapp2.WSGIApplication(routes, debug=True))
