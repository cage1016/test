import io
import pickle
import webapp2
import logging
import json
from delorean import Delorean
import datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api.taskqueue import taskqueue
from apiclient.http import MediaIoBaseDownload

from sendgrid import SendGridClient
from sendgrid import Mail

import settings
from models import Schedule, LogEmail, LogSendEmailFail, RecipientQueueData


class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    now = Delorean().truncate('minute')

    logging.info('match schedule_timestamp query = %f' % now.epoch())

    jobs = Schedule.query(Schedule.schedule_timestamp == now.epoch()).fetch()
    # jobs = Schedule.query(Schedule.schedule_timestamp == 1432634400.0).fetch()

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

      cursor = None
      while True:
        curs = Cursor(urlsafe=cursor)
        recipientQueues, next_curs, more = RecipientQueueData.query(
          ancestor=schedule_job.key).fetch_page(settings.QUEUE_CHUNKS_SIZE, start_cursor=curs)

        for index, r in enumerate(recipientQueues):
          params = {
            'schedule': pickle.dumps(schedule_job),
            'rqkey': r.key.urlsafe(),
            'content': content,
            'edm_object_name': schedule_job.edm_object_name
          }

          if index % 2 == 1:
            taskqueue.add(url='/tasks/worker', params=params, queue_name='worker')

          if index % 2 == 0:
            taskqueue.add(url='/tasks/worker2', params=params, queue_name='worker2')

        if more and next_curs:
          cursor = next_curs.urlsafe()

        else:
          break


class WorkHandler(webapp2.RequestHandler):
  def post(self):
    rqkey = self.request.get('rqkey')
    content = self.request.get('content')
    schedule = pickle.loads(self.request.get('schedule'))

    recipient_queue = ndb.Key(urlsafe=rqkey).get()

    try:
      recipients = json.loads(recipient_queue.data)

    except AttributeError:
      logging.error('AttributeError: urlsafe= %s, key= %s' % (rqkey, recipient_queue.key))
      logging.error('cancel mail worker!!')
      return

    logging.debug('/tasks/worker executed: send %d recipients.' % len(recipients))

    list_of_entity = []
    sendgrid = settings.SENDGRID[schedule.sendgrid_account]

    logging.debug(str(sendgrid))

    sg = SendGridClient(sendgrid.get('USERNAME'), sendgrid.get('PASSWORD'), raise_errors=True)
    for data in recipients:
      email = data['email']

      message = Mail()
      message.set_subject(schedule.subject)
      message.set_html(content)
      message.set_from('%s <%s>' % (schedule.sender_name, schedule.sender_email))
      message.add_to(email)
      message.add_category(schedule.category)

      # status = 200
      # msg = ''
      logging.debug(message)
      status, msg = sg.send(message)

      d = Delorean()
      if status == 200:
        log_email = LogEmail(
          sender='sendgrid',
          category=schedule.category,
          to=email,
          sender_name=schedule.sender_name,
          sender_email=schedule.sender_email,
          subject=schedule.subject,
          body=content,
          schedule_timestamp=schedule.schedule_timestamp,
          schedule_display=schedule.schedule_display,
          when_timestamp=d.epoch(),
          when_display=d.naive()
        )
        # list_of_entity.append(log_email)

      else:
        log_send_mail_fail = LogSendEmailFail(
          sender='sendgrid',
          category=schedule.category,
          to=email,
          sender_name=schedule.sender_name,
          sender_email=schedule.sender_email,
          subject=schedule.subject,
          body=content,
          schedule_timestamp=schedule.schedule_timestamp,
          schedule_display=schedule.schedule_display,
          when_timestamp=d.epoch(),
          when_display=d.naive(),
          reason=str(msg)
        )
        list_of_entity.append(log_send_mail_fail)

        logging.info('%s send fail: %s, %s' % email)

    futures = []
    futures.extend(ndb.put_multi_async(list_of_entity))
    ndb.Future.wait_all(futures)
    # TODO refactor
    # if any(f.get_exception() for f in futures):
    # raise ndb.Rollback()


