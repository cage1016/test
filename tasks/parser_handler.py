# -*- coding:utf-8 -*-

import pickle
import webapp2
import logging

from csv_parser import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))
    # parameters = {'sendgrid_account': u'mitacmax', 'daily_capacity': 1000,
    #               'edm_object_name': u'ipwarmup/cage@mitac.com.tw/index.htm', 'recipient_skip': 0, 'subject': u'xx',
    #               'replace_edm_csv_property': u'id,uid', 'sender_name': u'mitacmax', 'schedule_duration': 1,
    #               'hour_rate': 1, 'ip_counts': 1, 'bucket_name': u'cheerspoint-recipient',
    #               'sender_email': u'mitacmax@edm2.micloud.asia', 'category': 'xx', 'start_time': '2015/06/06 10:00',
    #               'txt_object_name': u'ipwarmup/cage@mitac.com.tw/kaichu1016_0375000.csv', 'reply_to': '',
    #               'type': u'ipwarmup'}

    sendgrid_account = parameters.get('sendgrid_account')
    subject = parameters.get('subject')
    sender_name = parameters.get('sender_name')
    sender_email = parameters.get('sender_email')

    category = parameters.get('category')
    reply_to = parameters.get('reply_to')
    type = parameters.get('type')

    txt_object_name = parameters.get('txt_object_name')
    edm_object_name = parameters.get('edm_object_name')
    replace_edm_csv_property = parameters.get('replace_edm_csv_property')
    bucket_name = parameters.get('bucket_name')

    schedule_duration = int(parameters.get('schedule_duration'))
    ip_counts = int(parameters.get('ip_counts'))

    recipient_skip = int(parameters.get('recipient_skip'))
    hour_rate = int(parameters.get('hour_rate'))
    start_time = parameters.get('start_time')
    daily_capacity = int(parameters.get('daily_capacity'))

    logging.info(parameters)

    parser = Parser(sendgrid_account,
                    subject,
                    sender_name,
                    sender_email,
                    category,
                    reply_to,
                    type,
                    txt_object_name,
                    edm_object_name,
                    replace_edm_csv_property,
                    bucket_name,
                    schedule_duration,
                    ip_counts,
                    recipient_skip,
                    hour_rate,
                    start_time,
                    daily_capacity)
    parser.run()