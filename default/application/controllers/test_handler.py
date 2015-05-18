__author__ = 'cage'

from google.appengine.ext.webapp.util import login_required
from webapp2_extras.appengine.users import admin_required
from google.appengine.ext import ndb

from application.controllers.basehandler import BaseHandler
import application.models as models


class TestAccountHandler(BaseHandler):
    @login_required
    @admin_required
    def get(self):
        delete_email = self.request.get('delete_email')
        if delete_email:

            data_ipwarmup = ndb.Key(urlsafe=delete_email).get()
            if data_ipwarmup:
                data_ipwarmup.key.delete()

        params = {}

        data_ipwarmups = models.IPWarmup().query().fetch()

        params.update(dict(data_ipwarmup=data_ipwarmups))

        self.render('test-account.html', **params)

    def post(self):
        new_ipwarmup = models.IPWarmup()
        new_ipwarmup.email = self.request.get('input_email')
        new_ipwarmup.put()

        self.redirect('/test_account')