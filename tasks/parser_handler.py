# -*- coding:utf-8 -*-

import pickle
import webapp2
import logging

from csv_parser import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    # parameters = pickle.loads(self.request.get('parameters'))
    parameters = {'category': 'mitac-warmup1-day', 'recipient_skip': 0, 'sender_name': u'kaichu',
                  'daily_capacity': 50000, 'start_time': '2015/05/26 18:00', 'ip_counts': 1,
                  'subject': u'my test 3', 'hour_rate': 1, 'bucket_name': u'cheerspoint-recipient',
                  'sender_email': u'kaichu1016@gmail.com',
                  'edm_object_name': u'ipwarmup/cage@mitac.com.tw/treemallmail.html',
                  'sendgrid_account': u'kaichu',
                  'txt_object_name': u'ipwarmup/cage@mitac.com.tw/kaichu1016_0002100.csv',
                  'type': u'ipwarmup', 'schedule_duration': 1}

    logging.info(parameters)

    parser = Parser(parameters)
    parser.run()