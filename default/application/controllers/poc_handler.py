
__author__ = 'cage'

from webapp2_extras.appengine.users import admin_required, login_required
from google.appengine.api import users
from google.appengine.ext import ndb

from application.controllers.basehandler import BaseHandler
import application.models as models


class POCHandler(BaseHandler):
    @login_required
    @admin_required
    def get(self):
        delete_email = self.request.get('delete_email')
        if delete_email:

            data_poc_account = ndb.Key(urlsafe=delete_email).get()
            if data_poc_account:
                data_poc_account.key.delete()

        params = {}

        data_poc_accounts = models.POCAccount().query().fetch()

        params.update(dict(data_poc_accounts=data_poc_accounts))

        self.render('poc-account.html', **params)

    def post(self):
        new_poc_account = models.POCAccount()
        new_poc_account.email = self.request.get('input_email')
        new_poc_account.put()

        self.redirect('/poc_account')