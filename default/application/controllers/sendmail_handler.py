__author__ = 'cage'

import json
import time
from datetime import datetime

from application.controllers.basehandler import UserHandler

from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api.taskqueue import taskqueue
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext import ndb

from application import blob_files, blob_serve, utils
from application.models import ScheduleEmail, Recipient, RecipientData, RecipientQueueData

CHUCKS_SIZE = 50


class SendMailHandler(UserHandler):
    def get_chucks(self, l, n):
        if n < 1:
            n = 1
        return [l[i:i + n] for i in range(0, len(l), n)]

    # @login_required
    def get(self):

        delete_sendmail = self.request.get('delete_sendmail')
        if delete_sendmail:
            data_sendmail = ndb.Key(urlsafe=delete_sendmail).get()

            data_sendmail.status = 'Deleting'
            data_sendmail.put()

            taskqueue.add(url='/tasks/delete/recipeint_queue',
                          params={'skey': data_sendmail.key.urlsafe()},
                          queue_name='recipient-queue-delete')

            self.redirect('/sendmail')

        params = {}

        ancestor_key = ndb.Key('User', self.user.email())
        data_recipeints = Recipient.query_recipient(ancestor_key).fetch()
        data_templates = blob_files.BlobFiles.query_template(ancestor_key).fetch()

        query = ScheduleEmail.query(ancestor=ancestor_key)
        query = query.filter(ScheduleEmail.status != 'Deleting')
        data_sendmails = query.fetch()

        params.update(dict(data_recipeints=data_recipeints,
                           data_templates=data_templates,
                           data_sendmails=data_sendmails))

        self.render('sendmail.html', **params)

    def post(self):

        sendmail_recipient = self.request.get('sendmail_recipient')
        sendmail_subject = self.request.get('sendmail_subject')
        sendmail_template = self.request.get('sendmail_template')
        sendmail_schedule = self.request.get('sendmail_schedule')
        sendmail_category = self.request.get('sendmail_category')
        sendmail_toname = self.request.get('sendmail_toname')
        sendmail_toemail = self.request.get('sendmail_toemail')

        data_recipient = ndb.Key(urlsafe=sendmail_recipient).get()
        data_template = ndb.Key(urlsafe=sendmail_template).get()

        ancestor_key = ndb.Key('User', self.user.email())
        key_name = '%s_%d' % (self.user.email, int(time.time()))

        new_sendmail = ScheduleEmail.get_or_insert(key_name, parent=ancestor_key)
        new_sendmail.subject = sendmail_subject
        new_sendmail.category = sendmail_category
        new_sendmail.toemail = sendmail_toemail
        new_sendmail.toname = sendmail_toname
        new_sendmail.schedule = utils.get_timestampe(datetime.strptime(sendmail_schedule, '%Y/%m/%d %H:%M'))
        new_sendmail.template = data_template.key
        new_sendmail.status = ''

        queue = []
        cursor = None
        while True:
            curs = Cursor(urlsafe=cursor)
            recipients_data, next_curs, more = RecipientData.query(
                ancestor=data_recipient.key).fetch_page(CHUCKS_SIZE, start_cursor=curs)

            queue = queue + [m.to_dict() for m in recipients_data]

            if more and next_curs:
                cursor = next_curs.urlsafe()

            else:
                break

        chucks = self.get_chucks(queue, CHUCKS_SIZE)

        list_of_entities = []
        for i in range(len(chucks)):
            rqd = RecipientQueueData(data=json.dumps(chucks[i]))
            list_of_entities.append(rqd)

        list_of_keys = ndb.put_multi(list_of_entities)
        new_sendmail.recipients = list_of_keys
        new_sendmail.recipients_count = len(queue)
        new_sendmail.recipients_name = data_recipient.name
        new_sendmail.template_name = data_template.filename
        new_sendmail.put()

        self.redirect('/sendmail')


