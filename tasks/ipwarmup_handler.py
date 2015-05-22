import pickle
import webapp2
import logging

import io
import csv
import datetime
import json

from delorean import parse

from google.appengine.ext.db import Error
from google.appengine.ext import ndb, deferred
from apiclient.http import MediaIoBaseDownload

from utils import ipwarmup_day_sending_rate

from models import RecipientData, Schedule, RecipientQueueData
import settings


class ParseCSVHandler(webapp2.RequestHandler):
  @settings.ValidateGCSWithCredential
  def post(self):

    parameters = pickle.loads(self.request.get('parameters'))
    txt_object_name = parameters.get('txt_object_name')
    edm_object_name = parameters.get('edm_object_name')
    bucket_name = parameters.get('bucket_name')
    ip_warmup_schedule_days = int(parameters.get('ip_warmup_schedule_days'))
    ip_counts = int(parameters.get('ip_counts'))
    category = parameters.get('category')
    recipient_skip = int(parameters.get('recipient_skip'))
    start_time = parameters.get('start_time')
    how_many_hours_do_the_job = int(parameters.get('how_many_hours_do_the_job'))

    logging.info(parameters)

    # --------
    # datetime manipuldate
    d = parse(start_time)

    # --------
    # download file from gcs
    file_name = txt_object_name.replace('/', '_')
    fh = io.FileIO(file_name, mode='wb')

    request = self.gcs_service.objects().get_media(bucket=bucket_name, object=txt_object_name)
    downloader = MediaIoBaseDownload(fh, request, chunksize=settings.CHUNKSIZE)

    done = False
    while done is False:
      status, done = downloader.next_chunk()
      if status:
        print "Download %d%%." % int(status.progress() * 100)
      print "Download Complete!"

    # sending rate
    # [91,83..]
    sending_rate = ipwarmup_day_sending_rate(ip_warmup_schedule_days, ip_counts, how_many_hours_do_the_job)
    logging.info(sending_rate)

    # handle csv parse
    with open(file_name, 'r') as csvfile:
      csv_reader = csv.DictReader(csvfile)

      index_of_hour = 0
      pre_index = -1
      count = 1

      save_queue = []
      save_queue_size = 50
      save_queue_index = 0
      new_ip_warmup_schedule = None
      for index, row in enumerate(csv_reader):

        if index_of_hour + 1 >= len(sending_rate):
          logging.error('txt length > capacity(%d)' % sum(sending_rate))
          break

        if index_of_hour > pre_index:
          _d = d.datetime + datetime.timedelta(hours=index_of_hour)
          _d = parse(_d.strftime('%Y-%m-%d %H:%M:%S'))

          new_ip_warmup_schedule = Schedule()
          new_ip_warmup_schedule.category = category

          new_ip_warmup_schedule.schedule_timestamp = _d.epoch()
          new_ip_warmup_schedule.schedule_display = _d.naive()

          new_ip_warmup_schedule.hour_delta = (index_of_hour + 1)
          new_ip_warmup_schedule.hour_rate = '1/%dhrs' % how_many_hours_do_the_job

          new_ip_warmup_schedule.txt_object_name = txt_object_name
          new_ip_warmup_schedule.edm_object_name = edm_object_name
          new_ip_warmup_schedule.put()

          pre_index = index_of_hour

        # debug only
        print index + 1, index_of_hour + 1, count

        if (index + 1) > recipient_skip:
          new_recipient_data = RecipientData(parent=new_ip_warmup_schedule.key)
          row['global_index'] = index + 1
          row['number_of_hour'] = index_of_hour + 1
          row['inner_index'] = count
          new_recipient_data.populate(**row)

          save_queue.append(new_recipient_data)
          save_queue_index = save_queue_index + 1

          if save_queue_index + 1 > save_queue_size:
            save_queue, save_queue_index, error = self.save(new_ip_warmup_schedule, save_queue)
            if error:
              logging.error('ipwarmup error occured: %s' % error)
              break

          count = count + 1

        if count > sending_rate[index_of_hour]:
          # update previous hour inner count
          new_ip_warmup_schedule.number_of_sending_mail = count - 1
          new_ip_warmup_schedule.put()

          save_queue, save_queue_index, error = self.save(new_ip_warmup_schedule, save_queue)
          if error:
            logging.error('ipwarmup error occured: %s' % error)
            break

          count = 1
          index_of_hour = index_of_hour + 1

      # update last inner count
      if new_ip_warmup_schedule:
        new_ip_warmup_schedule.hour_capacity = count - 1
        new_ip_warmup_schedule.put()

      # check save_queue if new_recipient_data < 50
      if len(save_queue) > 0:
        save_queue, save_queue_index, error = self.save(new_ip_warmup_schedule, save_queue)
        if error:
          logging.error('ipwarmup error occured: %s' % error)

  def save(self, new_ip_warmup_schedule, save_queue):
    """
    :param save_queue:
    :return: []:list_of_key, []:save_queue, 0:save_queue_index, error:error message
    """

    try:

      if len(save_queue) > 0:
        list_of_key = ndb.put_multi(save_queue)

        rqd = RecipientQueueData(data=json.dumps([x.to_dict() for x in save_queue]))
        rqd.put()

        new_ip_warmup_schedule.recipientQueue.append(rqd.key)
        new_ip_warmup_schedule.put()

        return [], 0, None

      else:
        return [], 0, None

    except Error, error:
      return [], 0, error
