# coding: utf-8

import io
import logging
import csv
import json
import time
import pickle
import tasks
from apiclient.http import MediaIoBaseDownload
from google.appengine.api import memcache
from apiclient.errors import HttpError
from httplib import HTTPException
from google.appengine.api import urlfetch_errors

from google.appengine.ext import ndb
from utils import enqueue_task
from GCSIterator import GCSIterator
from google.appengine import runtime

from utils import sending_rate, time_to_utc, time_add, timeit
import settings

from models import Schedule, RecipientQueueData, InvalidEmails
from validate_email import validate_email

import httplib2
from google.appengine.api import memcache
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials


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
    replace_edm_csv_property: html template replace property ex: <?pid?>:cmem_num,<?sd_id?>:pid

    schedule_duration: days, it will split to hours
    ip_counts: how many ip setting up in sendgrid

    recipient_skip: csv parser offset
    hour_rate: 1~24. how many hour will execute schedule job. 1/24: split to 24 jobs.
                                                              1/1: all receipient will send in one housr
    start_time: schedule job execute time. Taiwan time UTC+8
    daily_capacity:

    --------
    init_index: re-queue parameter, last parsecsv taskqueue index
    count: re-qeueu parameter, hourly capacity innert index
    total_count: re-qeueu parameter, schedule job capacity global index
    hour_index: re-queue parameter, hour cursor, start from 0
    last_hour_index: re-queue parameter, last hour cursor
    bytes_read: re-qeueue parameters, which byte has been read include current row
    csv_fieldnames: re-queue parameters, csv file header fielenames.
  """

  def __init__(self):
    self.save_queue = []
    self.SAVE_QUEUE_SIZE = settings.RECIPIENT_CHENKS_SIZE
    self.TASKQUEUE_SIZE = 500  # depend on taskqueue send data size limit. 500/10 = 50 entities
    self.list_of_rqd = []

    self.ts = time.time()

  def setup(self, parameters):
    self.sendgrid_account = parameters.get('sendgrid_account')
    self.subject = parameters.get('subject')
    self.sender_name = parameters.get('sender_name')
    self.sender_email = parameters.get('sender_email')

    self.category = parameters.get('category')
    self.reply_to = parameters.get('reply_to')
    self.type = parameters.get('type')

    self.txt_object_name = parameters.get('txt_object_name')
    self.edm_object_name = parameters.get('edm_object_name')
    self.bucket_name = parameters.get('bucket_name')
    self.replace_edm_csv_property = parameters.get('replace_edm_csv_property')

    self.schedule_duration = int(parameters.get('schedule_duration'))
    self.ip_counts = int(parameters.get('ip_counts'))

    self.recipient_skip = int(parameters.get('recipient_skip'))
    self.hour_rate = int(parameters.get('hour_rate'))
    self.start_time = parameters.get('start_time')
    self.daily_capacity = int(parameters.get('daily_capacity'))

    self.init_index = int(parameters.get('init_index')) if parameters.__contains__('init_index') else 0
    self.count = int(parameters.get('count')) if parameters.__contains__('count') else 0
    self.total_count = int(parameters.get('total_count')) if parameters.__contains__('total_count') else 0
    self.hour_index = int(parameters.get('hour_index')) if parameters.__contains__('hour_index') else 0
    self.last_hour_index = int(parameters.get('last_hour_index')) if parameters.__contains__('last_hour_index') else -1
    self.bytes_read = int(parameters.get('bytes_read')) if parameters.__contains__('bytes_read') else 0
    self.csv_fieldnames = parameters.get('csv_fieldnames')

    self.new_schedule = ndb.Key(urlsafe=parameters.get('new_schedule_key_urlsafe')).get() if parameters.__contains__(
      'new_schedule_key_urlsafe') else None

    self._index = 0
    self._capacity = 0
    self._progress = 0

  def read_edm_file(self, gcs_service, edm_object_name):
    data = memcache.get(edm_object_name)
    if data is not None:
      return data

    else:
      fh = io.BytesIO()
      request = gcs_service.objects().get_media(bucket=settings.BUCKET, object=edm_object_name.encode('utf8'))
      downloader = MediaIoBaseDownload(fh, request, chunksize=settings.CHUNKSIZE)
      done = False
      while not done:
        status, done = downloader.next_chunk()
        if status:
          logging.info('Download %d%%.' % int(status.progress() * 100))
        logging.info('Download %s Complete!' % edm_object_name)

      data = fh.getvalue()
      memcache.add(edm_object_name, data, settings.EDM_CONTENT_MEMCACHE_TIME)
      return data

  def run(self, parameters, MAX_TASKSQUEUE_EXECUTED_TIME=500):
    self._continue(parameters, MAX_TASKSQUEUE_EXECUTED_TIME)

  def _continue(self, parameters, MAX_TASKSQUEUE_EXECUTED_TIME=500):
    self.setup(parameters)

    credentials = AppAssertionCredentials(scope='https://www.googleapis.com/auth/devstorage.full_control')
    http = credentials.authorize(httplib2.Http(memcache))
    gcs_service = build('storage', 'v1', http=http, developerKey=settings.DEVELOPER_KEY)

    d = time_to_utc(self.start_time)

    enqueue = False

    try:
      # prepare sending rate
      # [91,83..], 2000 ex
      job_sending_rate, self._capacity = sending_rate(self.schedule_duration,
                                                      self.ip_counts,
                                                      self.hour_rate,
                                                      self.daily_capacity)
      logging.info(job_sending_rate)
      logging.info(self._capacity)

      request = gcs_service.objects().get_media(bucket=self.bucket_name, object=self.txt_object_name.encode('utf8'))
      self.gcs_iterator = GCSIterator(request, capacity=self._capacity, progress=self.bytes_read,
                                      chunksize=settings.CHUNKSIZE)

      if self.csv_fieldnames:
        self.csv_reader = csv.DictReader(self.gcs_iterator, skipinitialspace=True, delimiter=',',
                                         fieldnames=self.csv_fieldnames)

      else:
        self.csv_reader = csv.DictReader(self.gcs_iterator, skipinitialspace=True, delimiter=',')


      # check edm content
      try:
        content = self.read_edm_file(gcs_service, self.edm_object_name)
        test_ = unicode(content, 'utf8')
        logging.info('%s utf8 check ok.' % self.edm_object_name)

      except Exception:
        raise ValueError('%s encode utf8 error.' % self.edm_object_name)

      # start parse csv
      for i, row in enumerate(self.csv_reader):
        self._index = self.init_index + i

        # check recipients skip
        if self._index < self.recipient_skip:
          self.count += 1
          continue

        # create new schedule if hour index move
        if self.hour_index > self.last_hour_index:
          _d = time_add(d, self.hour_index)

          if job_sending_rate[self.hour_index] > 0:
            self.new_schedule = Schedule()
            self.new_schedule.sendgrid_account = self.sendgrid_account
            self.new_schedule.subject = self.subject
            self.new_schedule.sender_name = self.sender_name
            self.new_schedule.sender_email = self.sender_email
            self.new_schedule.category = self.category
            self.new_schedule.type = self.type

            self.new_schedule.schedule_timestamp = _d.epoch()
            self.new_schedule.schedule_display = _d.naive()

            self.new_schedule.hour_delta = (self.hour_index + 1)
            self.new_schedule.hour_rate = '1/%dhrs' % self.hour_rate

            self.new_schedule.txt_object_name = self.txt_object_name
            self.new_schedule.edm_object_name = self.edm_object_name
            self.new_schedule.replace_edm_csv_property = self.replace_edm_csv_property
            self.new_schedule.put()

          self.last_hour_index = self.hour_index

        # append extra index to data row
        if len(self.save_queue) >= self.SAVE_QUEUE_SIZE:
          self._to_put()

        # check hour capacity
        if self.count >= job_sending_rate[self.hour_index]:
          if job_sending_rate[self.hour_index] > 0:
            self._to_put()
            self._batch_write()

            # reset recipiensQueueData inner index, count
            self.count = 0

          # move hour index to next hour
          self.hour_index += 1

        # force put to taskqueue if hit max taskqueue send data size limit
        if self.count % self.TASKQUEUE_SIZE == 0 and self.count > 0:
          self._batch_write()

        # break if row index > totoal capacity
        if (self._index + 1) > self._capacity:
          logging.info('index (%d) >= capacity(%d). break parser.' % (self._index, self._capacity))
          break

        if (time.time() - self.ts).__int__() > MAX_TASKSQUEUE_EXECUTED_TIME:
          self.enqueue_handle()
          enqueue = True
          break

        # check email validation
        if validate_email(row.get('email')):
          row.update(gi=self._index, hr=self.hour_index, ii=self.count)
          self.save_queue.append(row)

        else:
          row.update(invalid=True,
                     sendgrid_account=self.sendgrid_account,
                     category=self.category,
                     schedule_subject=self.subject,
                     schedule_display=self.new_schedule.schedule_display,
                     hour_rate=self.hour_rate,
                     gi=self._index,
                     hr=self.hour_index)
          self.save_queue.append(row)

        self.count += 1
        self.total_count += 1

      if not enqueue:
        self._to_put()
        self._batch_write()

        self.finish()

    except (runtime.DeadlineExceededError,
            runtime.apiproxy_errors.CancelledError,
            runtime.apiproxy_errors.DeadlineExceededError,
            runtime.apiproxy_errors.OverQuotaError,
            urlfetch_errors.DeadlineExceededError,
            urlfetch_errors.Error,
            HTTPException) as e:

      logging.debug('error (%s): %s, auto enqueue_task again later.', e.__class__.__name__, e.message)

      self.enqueue_handle()

    except Exception as e:
      self.new_schedule = Schedule()
      self.new_schedule.sendgrid_account = self.sendgrid_account
      self.new_schedule.subject = self.subject
      self.new_schedule.schedule_timestamp = d.epoch()
      self.new_schedule.schedule_display = d.naive()
      self.new_schedule.sender_name = self.sender_name
      self.new_schedule.sender_email = self.sender_email
      self.new_schedule.category = self.category
      self.new_schedule.type = self.type
      self.new_schedule.txt_object_name = self.txt_object_name
      self.new_schedule.edm_object_name = self.edm_object_name
      self.new_schedule.replace_edm_csv_property = self.replace_edm_csv_property

      if isinstance(e, HttpError):
        self.new_schedule.error = '%s, %s' % (e.content, e.uri)

      else:
        self.new_schedule.error = '%s, %s' % (e.__class__.__name__, e.message)

      self.new_schedule.put()
      self.finish(self.new_schedule.error)

  def enqueue_handle(self):
    self._to_put()
    self._batch_write()

    parameters = {
      'sendgrid_account': self.sendgrid_account,
      'subject': self.subject,
      'sender_name': self.sender_name,
      'sender_email': self.sender_email,

      'category': self.category,
      'reply_to': self.reply_to,
      'type': self.type,

      'txt_object_name': self.txt_object_name,
      'edm_object_name': self.edm_object_name,
      'bucket_name': self.bucket_name,
      'replace_edm_csv_property': self.replace_edm_csv_property,

      'schedule_duration': self.schedule_duration,
      'ip_counts': self.ip_counts,

      'recipient_skip': self.recipient_skip,
      'hour_rate': self.hour_rate,
      'start_time': self.start_time,
      'daily_capacity': self.daily_capacity,

      'init_index': self._index,
      'count': self.count,
      'total_count': self.total_count,
      'hour_index': self.hour_index,
      'last_hour_index': self.last_hour_index,
      'bytes_read': self.gcs_iterator._bytes_read,
      'csv_fieldnames': self.csv_reader.fieldnames,

      'new_schedule_key_urlsafe': self.new_schedule.key.urlsafe()
    }

    new_parser = Parser()
    tasks.addTask(['parsecsv'], new_parser._continue, parameters, settings.MAX_TASKSQUEUE_EXECUTED_TIME)

  def finish(self, error=None):
    if error:
      logging.info('========== parser job throw execption (%s). done. ==========' % error)

    else:
      logging.info('========== parser job done. ==========')

  def _batch_write(self):
    if self.list_of_rqd:
      ndb.put_multi(self.list_of_rqd + [self.new_schedule])
      self.list_of_rqd = []

      percent = int(float(self.total_count) / float(self._capacity) * 100)
      if (percent % 10) == 0:
        if self._progress > -1:
          if percent > self._progress:
            logging.info('async has been process: %d (%d%%)' % (self.total_count, percent))

        self._progress = percent

  def _to_put(self):
    """
    pickle recipient list array to RecipientQueueData data property.

    1. when recipeints length >= SAVE_QUEUE_SIZE.
    2. move to next hourly.
    3. check last left recipient queue that have not saved.
    """

    if len(self.save_queue) > 0:
      valid_rows = [row for row in self.save_queue if not row.has_key('invalid')]
      invalid_rows = [row for row in self.save_queue if row.has_key('invalid')]

      rqd = RecipientQueueData(data=json.dumps(valid_rows), schedule_key=self.new_schedule.key)
      ies = [InvalidEmails.new(self.new_schedule.key, row) for row in invalid_rows]

      self.new_schedule.hour_capacity += len(valid_rows)
      self.new_schedule.invalid_email += len(invalid_rows)
      # self.list_of_rqd.extend(ndb.put_multi_async([rqd] + ies))
      self.list_of_rqd.extend([rqd] + ies)

      self.save_queue = []
      self.save_queue_index = 0
