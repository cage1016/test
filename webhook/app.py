# coding=utf-8

import logging
import webapp2
import json
import re

from google.appengine.api.taskqueue import taskqueue
from models import FlexWebhook


class WebhookHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to webhook page.")
    self.response.write("Welcome to the webhook module.")

  def post(self):
    taskqueue.add(url='/worker',
                  params={
                    'body': self.request.body
                  },
                  queue_name='webhook')


class WebookParserWorkerHandler(webapp2.RequestHandler):
  def post(self):

    events = json.loads(self.request.get('body'))

    logging.info('items= ' + str(events))

    for event in events:
      webhook = FlexWebhook()

      for key, value in event.items():
        if key == 'smtp-id':
          m = re.search(r'<(.*)>', value)
          webhook.populate(**{key: m.group(1)})

        else:
          webhook.populate(**{key: value})

      webhook.put()


class QueryHandler(webapp2.RequestHandler):
  def get(self):
    self.response.write("Welcome to the webhook module. query TODO.")


routes = [
  (r'/query', QueryHandler),
  (r'/worker', WebookParserWorkerHandler),
  (r'/', WebhookHandler)
]

router = webapp2.WSGIApplication(routes, debug=True)