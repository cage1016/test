__author__ = 'cage'

import logging
import json

from application.controllers.base import BaseRequestHandler, my_login_required, my_admin_required, report_user_required

from google.appengine.api import urlfetch
import urllib

import application.config as config

import cStringIO
from application import csv_writer

URL = 'https://sendgrid.com/api/'

SIMPLE_AUTHORIZTION = {
  'api_user': config.SENDGRID['USERNAME'],
  'api_key': config.SENDGRID['PASSWORD']
}


class BouncesHandler(BaseRequestHandler):
  @my_login_required
  @report_user_required
  def get(self):
    params = {}
    self.render('reports-base.html', **params)


class BlocksHandler(BaseRequestHandler):
  @my_login_required
  @report_user_required
  def get(self):
    params = {}
    self.render('reports-base.html', **params)


class InvalidEmailsHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    params = {}
    self.render('reports-base.html', **params)


class SpamHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    params = {}
    self.render('reports-base.html', **params)


class StatisticsHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    params = {}
    self.render('reports-base.html', **params)


class AdvanceStatisticsHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    params = {}
    self.render('reports-base.html', **params)


class EmailActivesHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    params = {}
    self.render('reports/email_activity.html', **params)


class SendgridAPIHandler(BaseRequestHandler):
  @my_login_required
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(config.SENDGRID))


class SendgridAPIHandler(BaseRequestHandler):
  @my_login_required
  def get(self, report):

    uri = URL + report + '?' + urllib.urlencode(SIMPLE_AUTHORIZTION) + '&' + self.request.query_string
    result = urlfetch.fetch(url=uri, deadline=60)

    logging.info('user fetch url: ' + uri)

    self.response.headers['Content-Type'] = 'application/json'
    if result.status_code == 200:
      self.response.out.write(json.dumps(result.content))
    else:
      self.response.out.write(json.dumps(result.content))


class DownloadCsvController(BaseRequestHandler):
  def get(self, report):
    uri = URL + report + '?' + urllib.urlencode(SIMPLE_AUTHORIZTION) + '&' + self.request.query_string
    result = urlfetch.fetch(url=uri, deadline=60)

    if result.status_code == 200:

      response = json.loads(result.content)
      output = cStringIO.StringIO()
      writer = csv_writer.GetJSONStringPrinter(output)
      writer.Output(response)

      out = output.getvalue()

      decoding = out.decode('utf-8')
      encoding = decoding.encode('utf-16')
      self.OutputCsv16(encoding, report)

      output.close()

    else:
      logging.error('fetch url error: %s' % uri)


  def OutputCsv16(self, csv_body, filename):
    """Renders CSV content.

    Args:
      csv_body: The TSV content to output.
    """
    self.response.headers['Content-Type'] = (
      'application/vnd.ms-excel; charset=UTF-16LE')
    self.response.headers['Content-Disposition'] = (
      'attachment; filename=%s.csv' % filename)
    self.response.out.write(csv_body)


reports_routes = [
  (r'/reports/bounces', BouncesHandler),
  (r'/reports/blocks', BlocksHandler),
  (r'/reports/invaid_emails', InvalidEmailsHandler),
  (r'/reports/spam', SpamHandler),
  (r'/reports/statistics', StatisticsHandler),
  (r'/reports/advance_statistics', AdvanceStatisticsHandler),
  (r'/reports/email_activity', EmailActivesHandler),
  (r'/reports/sendgrid/api/(\S+)', SendgridAPIHandler),
  (r'/reports/sendgrid/donwload/(\S+)', DownloadCsvController)
]