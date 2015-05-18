__author__ = 'cage'

import time
import csv

from application.controllers.basehandler import UserHandler
from google.appengine.api.taskqueue import taskqueue

from google.appengine.ext import ndb

from application.models import Recipient, RecipientData

CHUCKS_SIZE = 50


class RecipientsManageHandler(UserHandler):
    def get_chucks(self, l, n):
        if n < 1:
            n = 1
        return [l[i:i + n] for i in range(0, len(l), n)]

    def conver_to_utf8(self, row):

        # for key, value in row.items():
        # if value:
        # row[key] = repr(value)
        for key, value in row.items():
            if not isinstance(value, unicode):
                if not value is None:
                    row[key] = value.decode('utf-8')
                else:
                    row[key] = ''

        return row

    def get(self):

        delete_recipient = self.request.get('delete_recipient')
        if delete_recipient:

            data_recipeint = ndb.Key(urlsafe=delete_recipient).get()
            if data_recipeint:
                data_recipeint.status = 'Deleting'
                data_recipeint.put()

                taskqueue.add(url='/tasks/delete/recipeints',
                              params={'skey': data_recipeint.key.urlsafe()},
                              queue_name='recipient-delete')

                self.redirect('/recipients')

        params = {}

        ancestor_key = ndb.Key('User', self.user.email())

        query = Recipient.query(ancestor=ancestor_key)
        query = query.filter(Recipient.status != 'Deleting')

        data_recipeints = query.fetch()

        params.update(dict(data_recipeints=data_recipeints))

        self.render('recipients.html', **params)

    def post(self):

        recipients_name = self.request.get('recipients_name')
        file_data = self.request.get("recipients_file", default_value=None)
        if file_data:

            """
            handle file upload, parse csv and save to datastore
            """

            ancestor_key = ndb.Key('User', self.user.email())
            new_recipient = Recipient.get_or_insert(str(int(time.time())), parent=ancestor_key)

            content = self.request.POST.multi['recipients_file'].file.read()
            recipients_array = [s.strip() for s in content.split('\n') if s]
            fieldnames = [m for m in recipients_array[0].split(',')]

            reader = csv.DictReader(recipients_array[1:], fieldnames=fieldnames)

            chucks = self.get_chucks([row for row in reader], CHUCKS_SIZE)

            for i in range(len(chucks)):

                list_of_entities = []

                for row in chucks[i]:
                    new_recipient_data = RecipientData(parent=new_recipient.key)
                    new_recipient_data.populate(**self.conver_to_utf8(row))
                    list_of_entities.append(new_recipient_data)

                list_of_key = ndb.put_multi(list_of_entities)

            new_recipient.count = len(recipients_array) - 1 if len(recipients_array) > 1 else 0
            new_recipient.name = recipients_name
            new_recipient.put()

        self.redirect('/recipients')