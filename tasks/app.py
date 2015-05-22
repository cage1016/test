import webapp2
import logging
from ipwarmup_handler import ParseCSVHandler


class TasksHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the tasks module.")


routes = [
  (r'/tasks/parsecsv', ParseCSVHandler),
  (r'/.*', TasksHandler)
]

router = webapp2.WSGIApplication(routes, debug=True)
