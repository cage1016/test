__author__ = 'cage'

import json
import logging

import webapp2
from google.appengine.ext import ndb
from google.appengine.api import mail, mail_errors

import cloudstorage as gcs
from sendgrid import SendGridClient
from sendgrid import Mail
from application.models import LogEmail, LogSendEmailFail
from application import utils


GCS_UPLOAD_FOLDER = '/upload'

SENDER = '836641844649-q3vn5p272d020av7fvup2sfdroom4jmq@developer.gserviceaccount.com'
providr = 'sendgrid'

SENDGRID = {
    'USERNAME': 'kaichu',
    'PASSWORD': '75dkyz9n'
}


class WorkHandler(webapp2.RequestHandler):
    def post(self):

        skey = self.request.get('skey')
        i = int(self.request.get('i'))

        data_sendmail_schedule = ndb.Key(urlsafe=skey).get()

        if data_sendmail_schedule:
            # subject
            subject = data_sendmail_schedule.subject
            category = data_sendmail_schedule.category
            toname = data_sendmail_schedule.toname
            toemail = data_sendmail_schedule.toemail

            # read real html file from Google cloud storage
            blob = data_sendmail_schedule.template.get()
            with gcs.open(blob.gcs_filename, 'r') as gcs_file:
                content = gcs_file.read().replace('\n', '')

            recipeint = data_sendmail_schedule.recipients[i].get()

            for edata in json.loads(recipeint.data):
                email = edata['email']

                if providr == 'google':

                    try:
                        message = mail.EmailMessage(
                            sender='no-reply@example.com <%s>' % SENDER,
                            subject=subject)
                        message.to = email
                        message.body = content
                        message.send()

                        logging.info('%s send successful' % email)

                    except mail_errors.Error, error:

                        logSendEmailFail = LogSendEmailFail(
                            sender=SENDER,
                            category=category,
                            to=email,
                            toname=toname,
                            toemail=toemail,
                            subject=subject,
                            body=content,
                            schedule=data_sendmail_schedule.schedule,
                            when=utils.get_date_time('datetimeProperty'),
                            reason=str(error)
                        )
                        logSendEmailFail.put()

                        logging.error('An error occurred in MailWorker: %s' % error)

                if providr == 'sendgrid':

                    sg = SendGridClient(SENDGRID['USERNAME'], SENDGRID['PASSWORD'], raise_errors=True)

                    message = Mail()
                    message.set_subject(subject)
                    message.set_html(content)
                    # message.add_to_name(toname)
                    message.set_from('%s <%s>' % (toname, toemail))
                    message.add_to(email)
                    message.add_category(category)

                    status, msg = sg.send(message)

                    if status == 200:

                        data_sendmail_schedule.success_count = data_sendmail_schedule.success_count + 1

                        logEmail = LogEmail(
                            sender=SENDER,
                            category=category,
                            to=email,
                            toname=toname,
                            toemail=toemail,
                            subject=subject,
                            body=content,
                            schedule=data_sendmail_schedule.schedule,
                            when=utils.get_date_time('datetimeProperty')
                        )
                        logEmail.put()

                        logging.info('%s send successful' % email)

                    else:

                        data_sendmail_schedule.error_count = data_sendmail_schedule.error_count + 1

                        logSendEmailFail = LogSendEmailFail(
                            sender=SENDER,
                            category=category,
                            to=email,
                            toname=toname,
                            toemail=toemail,
                            subject=subject,
                            body=content,
                            schedule=data_sendmail_schedule.schedule,
                            when=utils.get_date_time('datetimeProperty'),
                            reason=str(msg)
                        )
                        logSendEmailFail.put()

                        logging.info('%s send fail: %s' % (email, msg))

            if data_sendmail_schedule.recipients_count == (
                        data_sendmail_schedule.success_count + data_sendmail_schedule.error_count):
                data_sendmail_schedule.status = 'Done'

            data_sendmail_schedule.put()