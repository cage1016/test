# coding=utf-8

from google.appengine.api import mail


class EMailer(object):
  @classmethod
  def send(self, subject, email, body):
    message = mail.EmailMessage(
      sender='{} <{}>'.format('Mimail 系統通知', 'cage-20160705-edm@appspot.gserviceaccount.com'),
      subject=subject,
      body=body,
      to=email
    )

    message.send()
