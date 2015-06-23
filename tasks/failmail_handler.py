import webapp2

from datastore_utils import Mapper
from models import ReTry

from mimail_client import MiMailClient2

import settings
import tasks


class RetryCheckHandler(webapp2.RequestHandler):
  def get(self):
    if ReTry.query().get() is not None:
      retry_send_mapper = RetrySendMapper(['retry-resend'])
      tasks.addTask(['retry-resend'], retry_send_mapper.run, batch_size=10)


class RetrySendMapper(Mapper):
  KIND = ReTry

  def __init__(self, tasks_queue):
    super(RetrySendMapper, self).__init__()
    self.tasks_queue = tasks_queue
    self.countdown_sec = 0

  def map(self, entity):
    return ([entity], [])

  # overwrite original batch write
  def _batch_write(self):
    if self.to_put:
      mimail_client2 = MiMailClient2()
      tasks.addTask(['worker', 'worker2'],
                    mimail_client2.resend,
                    retries=self.to_put,
                    _countdown=self.countdown_sec)

      self.to_put = []
      self.countdown_sec += 1
