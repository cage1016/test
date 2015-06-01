# -*- coding:utf-8 -*-

import pickle
import webapp2
import logging

from csv_parser import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))
    # parameters = {'category': 'mitac-warmup1-day', 'recipient_skip': 0, 'sender_name': u'kaichu',
    #               'daily_capacity': 1000, 'start_time': '2015/05/26 18:00', 'ip_counts': 1,
    #               'subject': u'my test 3', 'hour_rate': 1, 'bucket_name': u'cheerspoint-recipient',
    #               'sender_email': u'kaichu1016@gmail.com',
    #               'edm_object_name': u'ipwarmup/cage@mitac.com.tw/treemallmail.html',
    #               'sendgrid_account': u'kaichu',
    #               'txt_object_name': u'ipwarmup/cage@mitac.com.tw/點鑽驗收郵件帳號清單_20150505_with_mitac 10萬.csv',
    #               'type': u'ipwarmup', 'schedule_duration': 1}

    sendgrid_account = parameters.get('sendgrid_account')
    subject = parameters.get('subject')
    sender_name = parameters.get('sender_name')
    sender_email = parameters.get('sender_email')

    category = parameters.get('category')
    type = parameters.get('type')

    txt_object_name = parameters.get('txt_object_name')
    edm_object_name = parameters.get('edm_object_name')
    bucket_name = parameters.get('bucket_name')

    schedule_duration = int(parameters.get('schedule_duration'))
    ip_counts = int(parameters.get('ip_counts'))

    recipient_skip = int(parameters.get('recipient_skip'))
    hour_rate = int(parameters.get('hour_rate'))
    start_time = parameters.get('start_time')
    daily_capacity = int(parameters.get('daily_capacity'))

    logging.info(parameters)

    parser = Parser(sendgrid_account, subject, sender_name, sender_email, category, type, txt_object_name,
                    edm_object_name, bucket_name,
                    schedule_duration, ip_counts,
                    recipient_skip, hour_rate, start_time, daily_capacity)
    parser.run()
