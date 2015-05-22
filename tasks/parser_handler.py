import pickle
import webapp2
import logging

from csv_parser import Parser


class ParseCSVHandler(webapp2.RequestHandler):
  def post(self):
    parameters = pickle.loads(self.request.get('parameters'))

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

    logging.info(parameters)

    parser = Parser(subject, sender_name, sender_email, category, type, txt_object_name, edm_object_name, bucket_name, schedule_duration, ip_counts,
                    recipient_skip, hour_rate, start_time)
    parser.run()
