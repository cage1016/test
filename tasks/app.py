import webapp2
import logging
from parser_handler import ParseCSVHandler
from mailsend_handler import *
from delete_handler import *


class TasksHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the tasks module.")


routes = [
  (r'/tasks/parsecsv', ParseCSVHandler),

  (r'/tasks/schedule', ScheduleHandler),
  (r'/tasks/mailer', MailerHandler),
  (r'/tasks/worker', WorkHandler),
  (r'/tasks/worker2', WorkHandler),

  (r'/tasks/delete_resources', GCSResourcesDeleteHandler),
  (r'/tasks/delete_schedule', ScheduleDeleteHandler),

  (r'/.*', TasksHandler)
]

router = webapp2.WSGIApplication(routes, debug=True)
