__author__ = 'cage'

import logging
import webapp2

from google.appengine.ext import ndb
from google.appengine.api.taskqueue import taskqueue


class MailerHandler(webapp2.RequestHandler):
    def post(self):
        skey = self.request.get('skey')

        data_sendmail_schedule = ndb.Key(urlsafe=skey).get()

        if data_sendmail_schedule:

            logging.info('execute %s - %s' % ( data_sendmail_schedule.subject, data_sendmail_schedule.category))

            for i in range(0, len(data_sendmail_schedule.recipients)):
                taskqueue.add(url='/tasks/worker',
                              params={'skey': data_sendmail_schedule.key.urlsafe(), 'i': i},
                              queue_name='worker')