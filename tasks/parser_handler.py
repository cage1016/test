# -*- coding:utf-8 -*-

import pickle
import webapp2
import logging
import settings

from csv_parser import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))

    logging.info(parameters)

    parser = Parser(parameters)
    parser.run(MAX_TASKSQUEUE_EXECUTED_TIME=settings.MAX_TASKSQUEUE_EXECUTED_TIME)