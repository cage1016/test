__author__ = 'cage'

import webapp2
from application.controllers.base import BaseRequestHandler


class Handle403(BaseRequestHandler):
  def get(self):
    self.render("403.html")


class Handle404(BaseRequestHandler):
  def get(self):

    try:

      user = self.user
      self.render("404.html")

    except:
      self.render("welcome_404.html")


class Handle500(BaseRequestHandler):
  def get(self):
    self.render("500.html")