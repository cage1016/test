import io
import pickle
import webapp2
import logging
import json
import sys
from delorean import Delorean

from google.appengine import runtime
from google.appengine.api import memcache
from google.appengine.api import urlfetch_errors
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api.taskqueue import taskqueue
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from apiclient.http import MediaIoBaseDownload

from sendgrid import SendGridError, SendGridClientError, SendGridServerError
from sendgrid import SendGridClient
from sendgrid import Mail

import settings
from models import Schedule, LogEmail, LogSendEmailFail, RecipientQueueData

from utils import enqueue_task


class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    now = Delorean().truncate('minute')

    logging.info('match schedule_timestamp query = %f' % now.epoch())

    jobs = Schedule.query(Schedule.schedule_timestamp == now.epoch()).fetch()
    # jobs = Schedule.query(Schedule.schedule_timestamp == 1432634401.0).fetch()

    for job in jobs:
      job.schedule_executed = True
      job.put()

      logging.info('job schedule found!!, categroy:%s, hour_capacity= %d' % (job.category, job.hour_capacity))

      taskqueue.add(url='/tasks/mailer',
                    params={
                      'jkey': job.key.urlsafe()
                    },
                    queue_name='mailer')


class MailerHandler(webapp2.RequestHandler):
  def read_edm_file(self, edm_object_name):
    data = memcache.get(edm_object_name)
    if data is not None:
      return data

    else:
      fh = io.BytesIO()
      request = self.gcs_service.objects().get_media(bucket=settings.BUCKET, object=edm_object_name.encode('utf8'))
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

  @settings.ValidateGCSWithCredential
  def post(self):
    skey = self.request.get('jkey')

    schedule_job = ndb.Key(urlsafe=skey).get()

    if schedule_job:
      logging.info('execute %s @ %s' % (schedule_job.category, schedule_job.schedule_display))

      content = self.read_edm_file(schedule_job.edm_object_name)
      sendgrid = settings.SENDGRID[schedule_job.sendgrid_account]

      cursor = None
      while True:
        curs = Cursor(urlsafe=cursor)
        recipientQueues, next_curs, more = RecipientQueueData.query(
          ancestor=schedule_job.key).fetch_page(settings.QUEUE_CHUNKS_SIZE, start_cursor=curs)

        for index, r in enumerate(recipientQueues):
          params = {
            'schedule': pickle.dumps(schedule_job),
            'recipient_queue': r.data,
            'content': content,
            'edm_object_name': schedule_job.edm_object_name,
            'sendgrid_account': sendgrid['USERNAME'],
            'sendgrid_password': sendgrid['PASSWORD']
          }

          if index % 2 == 0:
            enqueue_task(url='/tasks/worker', queue_name='worker', params=params)

          if index % 2 == 1:
            enqueue_task(url='/tasks/worker2', queue_name='worker', params=params)

        if more and next_curs:
          cursor = next_curs.urlsafe()

        else:
          break


class WorkHandler(webapp2.RequestHandler):
  def post(self):
    """
    mailsend worker
    """

    schedule = pickle.loads(self.request.get('schedule'))
    content = self.request.get('content')
    recipients = json.loads(self.request.get('recipient_queue'))
    sendgrid_account = self.request.get('sendgrid_account')
    sendgrid_password = self.request.get('sendgrid_password')

    logging.debug('/tasks/worker executed: send %d recipients.' % len(recipients))
    logging.debug('sendgrid_account: %s' % sendgrid_account)
    logging.debug(recipients)

    self.futures = []
    sg = SendGridClient(sendgrid_account, sendgrid_password, raise_errors=True)

    for data in recipients:
      email = data['email']

      message = Mail()
      message.set_subject(schedule.subject)
      message.set_html(content)
      message.set_from('%s <%s>' % (schedule.sender_name, schedule.sender_email))
      if schedule.reply_to:
        message.set_replyto(schedule.reply_to)
      message.add_to(email)
      message.add_category(schedule.category)

      d = Delorean()
      try:
        # status = 200
        # msg = ''
        status, msg = sg.send(message)

        if status == 200:
          self.save_log_email(schedule, email, content, d)

        else:
          self.save_fail_log_email(schedule, email, content, d, msg)

      except SendGridClientError:
        logging.error('4xx error: %s' % msg)
        self.save_fail_log_email(schedule, email, content, d, msg)

      except SendGridServerError:
        logging.error('5xx error: %s' % msg)
        self.save_fail_log_email(schedule, email, content, d, msg)

      except SendGridError:
        logging.error('error: %s' % msg)
        self.save_fail_log_email(schedule, email, content, d, msg)

      except (
          taskqueue.Error,
          runtime.DeadlineExceededError,
          urlfetch_errors.DeadlineExceededError,
          runtime.apiproxy_errors.CancelledError,
          runtime.apiproxy_errors.DeadlineExceededError,
          runtime.apiproxy_errors.OverQuotaError) as e:

        logging.error('error: %s' % e)
        self.save_fail_log_email(schedule, email, content, d, e)

      except:
        type, e, traceback = sys.exc_info()
        logging.error('sys.exc_info error: %s' % e)

        self.save_fail_log_email(schedule, email, content, d, e)

    ndb.Future.wait_all(self.futures)
    # TODO refactor
    # if any(f.get_exception() for f in futures):
    # raise ndb.Rollback()


  def save_log_email(self, schedule, email, content, d):
    log_email = LogEmail(
      sender='sendgrid',
      category=schedule.category,
      to=email,
      reply_to=schedule.reply_to,
      sender_name=schedule.sender_name,
      sender_email=schedule.sender_email,
      subject=schedule.subject,
      body=content,
      schedule_timestamp=schedule.schedule_timestamp,
      schedule_display=schedule.schedule_display,
      when_timestamp=d.epoch(),
      when_display=d.naive()
    )
    self.futures.extend(ndb.put_multi_async([log_email]))

  def save_fail_log_email(self, schedule, email, content, d, error_msg):
    log_send_mail_fail = LogSendEmailFail(
      sender='sendgrid',
      category=schedule.category,
      to=email,
      reply_to=schedule.reply_to,
      sender_name=schedule.sender_name,
      sender_email=schedule.sender_email,
      subject=schedule.subject,
      body=content,
      schedule_timestamp=schedule.schedule_timestamp,
      schedule_display=schedule.schedule_display,
      when_timestamp=d.epoch(),
      when_display=d.naive(),
      reason=str(error_msg)
    )

    self.futures.extend(ndb.put_multi_async([log_send_mail_fail]))
    logging.info('%s send fail: %s, %s' % email)