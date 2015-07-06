import logging

import webapp2

import tasks

from mapper.mapper_async import AsyncMapper
from models import *


class ClearRecipientQueueDataHandler(webapp2.RequestHandler):
  def get(self):
    schedule_mapper = ClearRecipientQueueDataMapper(['schedule-delete-mapper'])
    tasks.addTask(['schedule-delete-mapper'], schedule_mapper.run)


class ClearReTryHandler(webapp2.RequestHandler):
  def get(self):
    clear_retry_mapper = ClearReTryMapper(['schedule-delete-mapper'])
    tasks.addTask(['schedule-delete-mapper'], clear_retry_mapper.run)


class ClearRecipientQueueDataMapper(AsyncMapper):
  KIND = RecipientQueueData

  def __init__(self, tasks_queue):
    super(ClearRecipientQueueDataMapper, self).__init__()
    self.tasks_queue = tasks_queue

  def map_fn(self, entities):
    for entity in entities:
      yield entity.key.delete_async()

  def enqueue(self):
    new_mapper = ClearRecipientQueueDataMapper(self.tasks_queue)
    tasks.addTask(self.tasks_queue, new_mapper._continue)

  def finish(self):
    logging.info('update schedule status to default done')


class ClearReTryMapper(AsyncMapper):
  KIND = ReTry

  def __init__(self, tasks_queue):
    super(ClearReTryMapper, self).__init__()
    self.tasks_queue = tasks_queue

  def map_fn(self, entities):
    for entity in entities:
      yield entity.key.delete_async()

  def enqueue(self):
    new_mapper = ClearReTryMapper(self.tasks_queue)
    tasks.addTask(self.tasks_queue, new_mapper._continue)

  def finish(self):
    logging.info('clear retry done.')
