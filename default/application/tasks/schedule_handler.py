__author__ = 'cage'

from datetime import datetime

import webapp2
from google.appengine.api.taskqueue import taskqueue

from pytz.gae import pytz
from application.models import ScheduleEmail
from application import utils


class ScheduleHandler(webapp2.RedirectHandler):
    def get(self):

        tz = pytz.timezone(pytz.country_timezones('tw')[0])
        sendmail_schedule = datetime.now(tz).strftime('%Y/%m/%d %H:%M')
        timestamp = utils.get_timestampe(datetime.strptime(sendmail_schedule, '%Y/%m/%d %H:%M'))

        data_sendmailSchedules = ScheduleEmail().query(
            ScheduleEmail.schedule == timestamp
        ).fetch()

        if data_sendmailSchedules:
            for dss in data_sendmailSchedules:
                dss.status = 'Sending'
                dss.put()

                taskqueue.add(url='/tasks/mailer',
                              params={'skey': dss.key.urlsafe()},
                              queue_name='mailer')

