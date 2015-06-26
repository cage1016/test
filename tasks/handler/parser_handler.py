# -*- coding:utf-8 -*-

import pickle
import webapp2
import tasks
import settings

from csv_parser2 import Parser
from models import Schedule


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))

    parser = Parser()
    r = tasks.addTask(['parsecsv'], parser.run, parameters, settings.MAX_TASKSQUEUE_EXECUTED_TIME).get_result()

    if not r:
      new_schedule = Schedule()
      new_schedule.sendgrid_account = parameters.get('sendgrid_account')
      new_schedule.subject = parameters.get('subject')
      new_schedule.sender_name = parameters.get('sender_name')
      new_schedule.sender_email = parameters.get('sender_email')

      new_schedule.category = parameters.get('category')
      new_schedule.reply_to = parameters.get('reply_to')
      new_schedule.type = parameters.get('type')

      new_schedule.txt_object_name = parameters.get('txt_object_name')
      new_schedule.edm_object_name = parameters.get('edm_object_name')
      new_schedule.bucket_name = parameters.get('bucket_name')
      new_schedule.replace_edm_csv_property = parameters.get('replace_edm_csv_property')

      new_schedule.schedule_duration = int(parameters.get('schedule_duration'))
      new_schedule.ip_counts = int(parameters.get('ip_counts'))

      new_schedule.recipient_skip = int(parameters.get('recipient_skip'))
      new_schedule.hour_rate = int(parameters.get('hour_rate'))
      new_schedule.start_time = parameters.get('start_time')
      new_schedule.daily_capacity = int(parameters.get('daily_capacity'))

      new_schedule.error = 'add schedule job taskqueue fail. retry later.'

      new_schedule.put()
