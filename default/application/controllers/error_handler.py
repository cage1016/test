import logging

# thrid-party imports
import webapp2
from webapp2_extras import sessions

# local imports
from application.controllers.base import BaseRequestHandler


class ErrorHandler(BaseRequestHandler):
  @webapp2.cached_property
  def session_store(self):
    return sessions.get_store(request=self.request)

  def render_exception(self, code, exception):
    # logging.exception(exception)
    self.response.set_status(code)
    self.render('/errors/{0}.html'.format(code), **{'msg': exception})


class Handle404(ErrorHandler):
  def get(self, exception):

    if self.logged_in:
      return self.render_exception(404, exception)

    else:
      self.response.set_status(404)
      self.render('/errors/welcome_404.html', **{'msg': exception})


class Handle500(ErrorHandler):
  def get(self, exception):
    return self.render_exception(500, exception)


class Handle403(ErrorHandler):
  def get(self, exception):
    return self.render_exception(403, exception)
