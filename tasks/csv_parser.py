# coding: utf-8

import logging
import csv
import datetime
import json

from google.appengine.ext import ndb
from GCSIterator import GCSIterator

from delorean import parse
from utils import sending_rate, time_to_utc, time_add
import settings

from models import Schedule, RecipientQueueData


class Parser(object):
  """
  Parser object: read csv file from google cloud storage and split recipients by sending rate

  :param
    sendgrid_account: sendgrid account use to call APIs

    subject: edm subject
    sender_name: edm sender name, should be comparable with sendgrid account
    sender_email: edm sender email, should be comparable with sendgrid account
    category: sendgrid cateogry, use to report query
    reply_to: optional, reply to
    type: 'ipwarmup' or '?' (to be done)
    txt_object_name: receipient list (.csv)
    edm_object_name: edm html file. (.html)
    bucket_name: gcs bucket name

    # sending rate parameters
    schedule_duration: days, it will split to hours
    ip_counts: how many ip setting up in sendgrid
    recipient_skip: csv parser offset
    hour_rate: 1~24. how many hour will execute schedule job. 1/24: split to 24 jobs.
                                                              1/1: all receipient will send in one housr
    daily_capacity:
    start_time: schedule job execute time. Taiwan time UTC+8
  """


  @settings.ValidateGCSWithCredential
  def __init__(self, sendgrid_account, subject, sender_name, sender_email, category, reply_to, type, txt_object_name,
               edm_object_name, replace_edm_csv_property, bucket_name,
               schedule_duration, ip_counts,
               recipient_skip, hour_rate, start_time, daily_capacity):


    self.sendgrid_account = sendgrid_account
    self.subject = subject
    self.sender_name = sender_name
    self.sender_email = sender_email
    self.category = category
    self.reply_to = reply_to
    self.type = type
    self.txt_object_name = txt_object_name
    self.edm_object_name = edm_object_name
    self.replace_edm_csv_property = replace_edm_csv_property
    self.bucket_name = bucket_name
    self.schedule_duration = schedule_duration
    self.ip_counts = ip_counts
    self.recipient_skip = recipient_skip
    self.hour_rate = hour_rate
    self.start_time = start_time
    self.daily_capacity = daily_capacity

    self.save_queue = []
    self.SAVE_QUEUE_SIZE = settings.RECIPIENT_CHENKS_SIZE
    self.save_queue_index = 0
    self.new_schedule = None

    self.list_of_rqd = []
    self.TASKQUEUE_SIZE = 500  # depend on taskqueue send data size limit.

  def run(self):
    """
    parse CSV file
    """

    # datetime manipulate
    # all datastore store datetime as utc time
    d = time_to_utc(self.start_time)

    # prepare sending rate
    # [91,83..], 2000 ex
    job_sending_rate, capacity = sending_rate(self.schedule_duration,
                                              self.ip_counts,
                                              self.hour_rate,
                                              self.daily_capacity)
    logging.info(job_sending_rate)
    logging.info(capacity)

    # prepare csv recipient array
    index_of_hour = 0
    pre_index = -1
    count = 0

    request = self.gcs_service.objects().get_media(bucket=self.bucket_name, object=self.txt_object_name.encode('utf8'))
    for index, row in enumerate(
        csv.DictReader(GCSIterator(request, chunksize=settings.CHUNKSIZE), skipinitialspace=True, delimiter=',')):

      # break if row index > totoal capacity
      if index >= capacity:
        logging.info('index (%d) > capacity(%d). break parser.' % (index, capacity))
        break

      if index_of_hour + 1 > len(job_sending_rate):
        logging.error('custom error: txt length > capacity(%d)' % capacity)
        break

      if index_of_hour > pre_index:
        _d = time_add(d, index_of_hour)

        if job_sending_rate[index_of_hour] > 0:
          self.new_schedule = Schedule()
          self.new_schedule.sendgrid_account = self.sendgrid_account
          self.new_schedule.subject = self.subject
          self.new_schedule.sender_name = self.sender_name
          self.new_schedule.sender_email = self.sender_email
          self.new_schedule.category = self.category
          self.new_schedule.type = self.type

          self.new_schedule.schedule_timestamp = _d.epoch()
          self.new_schedule.schedule_display = _d.naive()

          self.new_schedule.hour_delta = (index_of_hour + 1)
          self.new_schedule.hour_rate = '1/%dhrs' % self.hour_rate

          self.new_schedule.txt_object_name = self.txt_object_name
          self.new_schedule.edm_object_name = self.edm_object_name
          self.new_schedule.replace_edm_csv_property = self.replace_edm_csv_property
          self.new_schedule.put()

        pre_index = index_of_hour

      # debug only
      # print index + 1, index_of_hour + 1, count

      # skip check
      if (index + 1) > self.recipient_skip:
        # how many recipients for each RecipientQueueData entity.
        if self.save_queue_index >= self.SAVE_QUEUE_SIZE:
          self.save()

        new_recipient_data = {}
        row['global_index'] = index + 1
        row['number_of_hour'] = index_of_hour + 1
        row['inner_index'] = count
        new_recipient_data.update(row)

        self.save_queue_index += 1
        self.save_queue.append(new_recipient_data)

        count += 1

      # force put to taskququ if hour sending rate is full
      if count >= job_sending_rate[index_of_hour]:
        # update previous hour inner count
        if job_sending_rate[index_of_hour] > 0:
          self.save()
          self.add_put_task(count)

          count = 0

        index_of_hour = index_of_hour + 1

      # force put to taskqueue if hit max taskququ send data size limit
      if (count - 1) % self.TASKQUEUE_SIZE == 0 and (count - 1) > 0:
        self.add_put_task(count - 1)


    # check left self.save_queue have not saved.
    if len(self.save_queue) > 0:
      self.save()
      self.add_put_task(count)

    logging.info('========== parser job done. ==========')


  def add_put_task(self, c):
    """
    add put task: really execute save to datastore.
    """

    ndb.Future.wait_all(self.list_of_rqd)
    self.new_schedule.put()
    logging.info('has been process: %d' % c)


  def save(self):
    """
    pickle recipient list array to RecipientQueueData data property.

    1. when recipeints length >= SAVE_QUEUE_SIZE.
    2. move to next hourly.
    3. check last left recipient queue that have not saved.
    """

    if len(self.save_queue) > 0:
      rqd = RecipientQueueData(parent=self.new_schedule.key, data=json.dumps(self.save_queue))
      self.new_schedule.hour_capacity += len(self.save_queue)
      self.list_of_rqd.extend(ndb.put_multi_async([rqd]))

      self.save_queue = []
      self.save_queue_index = 0