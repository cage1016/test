# coding=utf-8

from google.appengine.api import mail


class EMailer(object):
  @classmethod
  def send(self, subject, email, body):
    message = mail.EmailMessage(
      sender='{} <{}>'.format('Mimail 系統通知', 'mitac-cheerspoint-v20150518@appspot.gserviceaccount.com'),
      subject=subject,
      body=body,
      to=email
    )

    message.send()
