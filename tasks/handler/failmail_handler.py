import logging
import webapp2

from models import ReTry
from mimail_client import MiMailClient2
from mapper.mapper_async import AsyncMapper
import tasks


class RetryCheckHandler(webapp2.RequestHandler):
  def get(self):
    if ReTry.query().get() is not None:
      tasks_queue = ['retry-resend']
      retry_send_async_mapper = RetrySendAsyncMapper(tasks_queue)
      tasks.addTask(tasks_queue, retry_send_async_mapper.run)


class RetrySendAsyncMapper(AsyncMapper):
  KIND = ReTry

  def __init__(self, tasks_queue):
    super(RetrySendAsyncMapper, self).__init__()
    self.tasks_queue = tasks_queue
    self.countdown_sec = 0
    self.retry_count = 0
    self.mimail_client2 = MiMailClient2()

  def map_fn(self, items):
    tasks.addTask(['worker', 'worker2'],
                  self.mimail_client2.resend,
                  retries=items,
                  _countdown=self.countdown_sec)

    self.countdown_sec += 1
    self.retry_count += len(items)

    for item in items:
      yield item.key.delete_async()

  def enqueue(self, next_cursor):
    tasks.addTask(self.tasks_queue, self._continue, next_cursor)

  def finish(self, more):
    if more:
      logging.info('retry count= %d (have not finished)', self.retry_count)

    else:
      logging.info('retry finished count= %d ', self.retry_count)
