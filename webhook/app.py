import logging
import webapp2
import json

from models import FlexWebhook


class WebhookHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to webhook page.")
    self.response.write("Welcome to the webhook module.")

  def post(self):
    try:

      events = json.loads(self.request.body)
      logging.info('items= ' + str(events))

      for event in events:
        webhook = FlexWebhook()

        for key, value in event.items():
          webhook.populate(**{key: value})

        webhook.put()

      self.response.headers['Content-Type'] = 'text/plain'
      self.response.write('Successfully added new todo')

    except:

      raise Exception("Error: could not complete request")


class QueryHandler(webapp2.RequestHandler):
  def get(self):
    self.response.write("Welcome to the webhook module. query TODO.")


routes = [
  (r'/webhook/query', QueryHandler),
  (r'/.*', WebhookHandler)
]

router = webapp2.WSGIApplication(routes, debug=True)