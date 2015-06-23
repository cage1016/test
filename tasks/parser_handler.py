# -*- coding:utf-8 -*-

import pickle
import webapp2
import tasks

from csv_parser2 import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))

    parser = Parser()
    tasks.addTask(['parsecsv'], parser.run, parameters)