__author__ = 'cage'

from application.controllers.base import BaseRequestHandler, my_login_required


class SendMailHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    params = {}

    self.render('mail/mail_list.html', **params)