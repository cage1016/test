# -*- coding:utf-8 -*-

import pickle
import webapp2
import logging

from csv_parser import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))

    logging.info(parameters)

    parser = Parser(parameters)
    parser.run(MAX_TASKSQUEUE_EXECUTED_TIME=400)