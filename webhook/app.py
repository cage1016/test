# coding=utf-8

import logging
import webapp2
import json
import time
import pickle

from google.appengine.ext import ndb
from models import CheerspointWebhook

from utils import enqueue_task, timeit, grouper
import settings


class WebhookHandler(webapp2.RequestHandler):
  def get(self):
    logging.info("Get request to webhook page.")
    self.response.write("Welcome to the webhook module.")

  def post(self):
    events = json.loads(self.request.body)
    logging.info(events)
    enqueue_task(url='/parse',
                 queue_name='parse',
                 params={
                   'events': pickle.dumps(events)
                 })


# https://cloud.google.com/bigquery/streaming-data-into-bigquery
class WebookParserHandler(webapp2.RequestHandler):
  @timeit
  def post(self):
    events = pickle.loads(self.request.get('events'))

    for chunks in grouper(events, settings.EVENT_CHUNKS):
      enqueue_task(url='/worker',
                   queue_name='webhook',
                   params={
                     'entities': pickle.dumps(map(lambda chunk: CheerspointWebhook.new(chunk), chunks))
                   })

      for c in chunks:
        events.remove(c)

      if (time.time() - self.ts).__int__() > settings.MAX_TASKSQUEUE_EXECUTED_TIME:
        enqueue_task(url='/parse',
                     queue_name='parse',
                     params={
                       'events': pickle.dumps(events)
                     })

        break


class WebookParserWorkerHandler(webapp2.RequestHandler):
  @ndb.toplevel
  def post(self):
    entities = pickle.loads(self.request.get('entities'))
    yield ndb.put_multi_async(entities=entities)


routes = [
  (r'/parse', WebookParserHandler),
  (r'/worker', WebookParserWorkerHandler),
  (r'/', WebhookHandler)
]

router = webapp2.WSGIApplication(routes, debug=True)