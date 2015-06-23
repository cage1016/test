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


class UpdateScheduleHandler(webapp2.RequestHandler):
  def get(self):
    schedule_mapper = ScheduleUpdateMapper(['schedule-delete-mapper'])
    tasks.addTask(['schedule-delete-mapper'], schedule_mapper.run)


class ScheduleUpdateMapper(Mapper):
  KIND = Schedule

  def __init__(self, tasks_queue):
    super(ScheduleUpdateMapper, self).__init__()
    self.tasks_queue = tasks_queue

  def map(self, entity):
    entity.status = ''

    return ([entity], [])

  def finish(self):
    logging.info('update schedule status to default done')


routes = [
  (r'/tasks/parsecsv', ParseCSVHandler),
  (r'/tasks/schedule', ScheduleHandler),

  (r'/tasks/delete_resources', GCSResourcesDeleteHandler),
  (r'/tasks/delete_schedule', ScheduleDeleteHandler),
  (r'/tasks/check_schedule_delete', ScheduleDeleteCheckHandler),

  (r'/tasks/retry_check', RetryCheckHandler),
  # (r'/tasks/update_schedule', UpdateScheduleHandler),

  webapp2.Route('/tasks/_cb/deferred/<module>/<name>', tasks.DeferredHandler),

  (r'/.*', TasksHandler)
]

router = ndb.toplevel(webapp2.WSGIApplication(routes, debug=True))
