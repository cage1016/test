import webapp2
import logging

from google.appengine.ext import ndb, deferred

class TasksHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the tasks module.")


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):

    urlsafe = self.request.get('urlsafe')

    logging.info(urlsafe)

routes = [
  (r'/tasks/parsecsv', ParseCSVHandler),
  (r'/.*', TasksHandler)
]

router = webapp2.WSGIApplication(routes, debug=True)
