import logging

import io
import csv
import datetime
import json
import re

from delorean import parse

from google.appengine.ext import ndb
from google.appengine.ext.db import Error
from apiclient.http import MediaIoBaseDownload

from utils import ipwarmup_day_sending_rate, time_to_utc

from models import Schedule, RecipientQueueData
import settings


class Parser(object):
  @settings.ValidateGCSWithCredential
  def __init__(self, sendgrid_account, subject, sender_name, sender_email, category, type, txt_object_name,
               edm_object_name, bucket_name,
               schedule_duration, ip_counts,
               recipient_skip, hour_rate, start_time, daily_capacity):


    self.sendgrid_account = sendgrid_account
    self.subject = subject
    self.sender_name = sender_name
    self.sender_email = sender_email
    self.category = category
    self.type = type
    self.txt_object_name = txt_object_name
    self.edm_object_name = edm_object_name
    self.bucket_name = bucket_name
    self.schedule_duration = schedule_duration
    self.ip_counts = ip_counts
    self.recipient_skip = recipient_skip
    self.hour_rate = hour_rate
    self.start_time = start_time
    self.daily_capacity = daily_capacity

    self.save_queue = []
    self.save_queue_size = settings.RECIPIENT_CHENKS_SIZE
    self.save_queue_index = 0
    self.new_ip_warmup_schedule = None

    self.futures = []

  def read_csv_file(self):
    """
    read csv file from Goolge Cloud Storage

    :return: csv array list
    """

    fh = io.BytesIO()
    request = self.gcs_service.objects().get_media(bucket=self.bucket_name, object=self.txt_object_name.encode('utf8'))
    downloader = MediaIoBaseDownload(fh, request, chunksize=settings.CHUNKSIZE)
    done = False
    logging.info('Start Downloading %s!' % self.txt_object_name)
    while not done:
      status, done = downloader.next_chunk()
      if status:
        logging.info('Download %d%%.' % int(status.progress() * 100))

    logging.info('Download done!')
    
    return re.split('\r|\n|\r\n', fh.getvalue())

  def run(self):
    # --------
    # datetime manipuldate
    d = time_to_utc(self.start_time)
    # --------

    # prepare sending rate
    # [91,83..]
    sending_rate = ipwarmup_day_sending_rate(self.schedule_duration,
                                             self.ip_counts,
                                             self.hour_rate,
                                             self.daily_capacity)
    capacity = sum(sending_rate)
    logging.info(sending_rate)
    logging.info(capacity)

    # prepare csv recipient array
    csv_array_list = self.read_csv_file()
    csv_reader = csv.DictReader(csv_array_list)

    index_of_hour = 0
    pre_index = -1
    count = 1

    for index, row in enumerate(csv_reader):

      # break if row index > totoal capacity
      if index >= capacity:
        logging.info('index (%d) > capacity(%d). break parser.' % (index, capacity))
        break

      if index_of_hour + 1 > len(sending_rate):
        logging.error('custom error: txt length > capacity(%d)' % capacity)
        break

      if index_of_hour > pre_index:
        _d = d.datetime + datetime.timedelta(hours=index_of_hour)
        _d = parse(_d.strftime('%Y-%m-%d %H:%M:%S'))

        if sending_rate[index_of_hour] > 0:
          self.new_ip_warmup_schedule = Schedule()
          self.new_ip_warmup_schedule.sendgrid_account = self.sendgrid_account
          self.new_ip_warmup_schedule.subject = self.subject
          self.new_ip_warmup_schedule.sender_name = self.sender_name
          self.new_ip_warmup_schedule.sender_email = self.sender_email
          self.new_ip_warmup_schedule.category = self.category
          self.new_ip_warmup_schedule.type = self.type

          self.new_ip_warmup_schedule.schedule_timestamp = _d.epoch()
          self.new_ip_warmup_schedule.schedule_display = _d.naive()

          self.new_ip_warmup_schedule.hour_delta = (index_of_hour + 1)
          self.new_ip_warmup_schedule.hour_rate = '1/%dhrs' % self.hour_rate

          self.new_ip_warmup_schedule.txt_object_name = self.txt_object_name
          self.new_ip_warmup_schedule.edm_object_name = self.edm_object_name
          self.new_ip_warmup_schedule.put()

        pre_index = index_of_hour

      # debug only
      # print index + 1, index_of_hour + 1, count

      if (index + 1) > self.recipient_skip:
        new_recipient_data = {}
        row['global_index'] = index + 1
        row['number_of_hour'] = index_of_hour + 1
        row['inner_index'] = count
        new_recipient_data.update(row)

        self.save_queue.append(new_recipient_data)
        self.save_queue_index = self.save_queue_index + 1

        if self.save_queue_index + 1 > self.save_queue_size:
          error = self.save()
          if error:
            logging.error('ipwarmup error occured: %s' % error)
            break

        count = count + 1

      if count > sending_rate[index_of_hour]:
        # update previous hour inner count
        if sending_rate[index_of_hour] > 0:
          self.new_ip_warmup_schedule.number_of_sending_mail = count - 1
          self.new_ip_warmup_schedule.put()

          error = self.save()
          if error:
            logging.error('ipwarmup error occured: %s' % error)
            break

          count = 1
        index_of_hour = index_of_hour + 1

      if count % 1000 == 0:
        logging.info('has been process: %d' % count)


    # check self.save_queue if new_recipient_data < 50
    if len(self.save_queue) > 0:
      error = self.save()
      if error:
        logging.error('ipwarmup error occured: %s' % error)

    ndb.Future.wait_all(self.futures)
    logging.info('parser end')

  def save(self):
    """
    :return:  error:error message
    """
    try:

      if len(self.save_queue) > 0:

        rqd = RecipientQueueData(parent=self.new_ip_warmup_schedule.key, data=json.dumps(self.save_queue))
        self.new_ip_warmup_schedule.hour_capacity += len(self.save_queue)
        self.futures.extend(ndb.put_multi_async([rqd, self.new_ip_warmup_schedule]))

        self.save_queue = []
        self.save_queue_index = 0

        return None

      else:
        self.save_queue = []
        self.save_queue_index = 0
        return None

    except Error, error:
      self.save_queue = []
      self.save_queue_index = 0

      return error