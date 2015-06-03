__author__ = 'cage'

from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import BadValueError
from application.controllers.base import BaseRequestHandler, my_admin_required
from application.models import User


class AccountManagementHandler(BaseRequestHandler):
  @my_admin_required
  def get(self):
    params = {}

    users = User.query().fetch()

    params.update(users=users)

    self.render('account/account_management.html', **params)


class AccountManagementNewAccountHandler(BaseRequestHandler):
  @my_admin_required
  def get(self):
    params = {}
    self.render('account/account_management_new.html', **params)

  def post(self):
    new_email = self.request.get('email')
    new_account_enabled = True if self.request.get('accountEnabled') == 'on' else False
    new_report_enabled = True if self.request.get('reportEnabled') == 'on' else False
    new_is_admin = True if self.request.get('isAdmin') == 'on' else False
    new_description = self.request.get('description')

    auth_id = 'google:%s' % new_email

    data_user = User.get_by_id(auth_id)
    if data_user:
      params = {}
      params.update(ndb_user=data_user, error_message='account exist')
      self.render('account/account_management_new.html', **params)
      return

    else:
      user = User.get_or_insert(auth_id)
      if user:
        user.email = new_email
        user.account_enabled = new_account_enabled
        user.report_enabled = new_report_enabled
        user.is_admin = new_is_admin
        user.description = new_description

        user.put()

    self.redirect('/account_management')


class AccountManagementEditHandler(BaseRequestHandler):
  @my_admin_required
  def get(self, urlsafe):
    params = {}

    try:
      ndb_user = ndb.Key(urlsafe=urlsafe).get()
    except BadValueError:
      self.redirect('/account_management')
      return

    params.update(ndb_user=ndb_user)

    self.render('account/account_management_edit.html', **params)


  def post(self, urlsafe):

    try:
      user = ndb.Key(urlsafe=urlsafe).get()
    except BadValueError:
      self.redirect('/account_management')
      return

    new_account_enabled = True if self.request.get('accountEnabled') == 'on' else False
    new_report_enabled = True if self.request.get('reportEnabled') == 'on' else False
    new_is_admin = True if self.request.get('isAdmin') == 'on' else False

    user.report_enabled = new_report_enabled
    user.account_enabled = new_account_enabled
    user.is_admin = new_is_admin
    user.put()

    self.redirect('/account_management')


class AccountManagementDeleteAccountHandler(BaseRequestHandler):
  @my_admin_required
  def get(self, urlsafe):

    try:
      ndb_user = ndb.Key(urlsafe=urlsafe).get()
    except BadValueError:
      self.redirect('/account_management')
      return

    ndb_user.key.delete()

    self.redirect('/account_management')


account_management_route = [
  ('/account_management', AccountManagementHandler),
  ('/account_management/new', AccountManagementNewAccountHandler),
  ('/account_management/delete/([^/]+)?', AccountManagementDeleteAccountHandler),
  ('/account_management/([^/]+)?', AccountManagementEditHandler)
]