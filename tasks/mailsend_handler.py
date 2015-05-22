import io
import os.path
import pickle
import webapp2
import logging
import json
from delorean import Delorean

from models import Schedule, LogEmail, LogSendEmailFail
from google.appengine.ext import ndb
from google.appengine.api.taskqueue import taskqueue
from apiclient.http import MediaIoBaseDownload

from sendgrid import SendGridClient
from sendgrid import Mail

import settings


class ScheduleHandler(webapp2.RequestHandler):
  def get(self):
    timestamp = Delorean().epoch()

    logging.info('cron job timestamp=%f' % timestamp)

    #
    logging.info('manual setting debug timestamp= 1433322000.0 for testing')
    timestamp = 1433116800.0

    jobs = Schedule.query(Schedule.schedule_timestamp == timestamp).fetch()

    for job in jobs:
      taskqueue.add(url='/tasks/mailer',
                    params={
                      'jkey': job.key.urlsafe()
                    },
                    queue_name='mailer')


class MailerHandler(webapp2.RequestHandler):
  def post(self):
    skey = self.request.get('jkey')

    schedule_job = ndb.Key(urlsafe=skey).get()

    if schedule_job:
      logging.info('execute %s @ %s' % (schedule_job.category, schedule_job.schedule_display))

      for index, recipient_queue in enumerate(schedule_job.recipientQueue):
        logging.info('%d, %s' % (index, recipient_queue.urlsafe()))
        taskqueue.add(url='/tasks/worker',
                      params={
                        'schedule': pickle.dumps(schedule_job),
                        'rqkey': recipient_queue.urlsafe(),
                        'edm_object_name': schedule_job.edm_object_name
                      },
                      queue_name='worker')


class WorkHandler(webapp2.RequestHandler):
  def read_edm_file(self, edm_object_name):
    content = None
    file_name = edm_object_name.replace('/', '_')

    if os.path.exists(file_name):
      with open(file_name, 'r') as f:
        content = f.read()
      return content

    else:
      file_name = edm_object_name.replace('/', '_')
      fh = io.FileIO(file_name, mode='wb')

      request = self.gcs_service.objects().get_media(bucket=settings.BUCKET, object=edm_object_name.encode('utf8'))
      downloader = MediaIoBaseDownload(fh, request, chunksize=settings.CHUNKSIZE)

      done = False
      while done is False:
        status, done = downloader.next_chunk()
        if status:
          print "Download %d%%." % int(status.progress() * 100)
        print "Download Complete!"

      with open(file_name, 'r') as f:
        content = f.read()
      return content

  @settings.ValidateGCSWithCredential
  def post(self):
    rqkey = self.request.get('rqkey')
    edm_object_name = self.request.get('edm_object_name')
    schedule = pickle.loads(self.request.get('schedule'))

    logging.info(schedule)

    content = self.read_edm_file(edm_object_name)
    # logging.info(content)

    recipient_queue = ndb.Key(urlsafe=rqkey).get()

    for data in json.loads(recipient_queue.data):
      email = data['email']

      logging.info('sendgrid send = %s' % email)

      sg = SendGridClient(settings.SENDGRID['USERNAME'], settings.SENDGRID['PASSWORD'], raise_errors=True)

      message = Mail()
      message.set_subject(schedule.subject)
      message.set_html(content)
      message.set_from('%s <%s>' % (schedule.sender_name, schedule.sender_email))
      message.add_to(email)
      message.add_category(schedule.category)

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
        log_email.put()

        logging.info('%s send successful' % email)

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
        log_send_mail_fail.put()

        logging.info('%s send successful' % email)
