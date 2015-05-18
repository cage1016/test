__author__ = 'cage'

import os

import webapp2
from webapp2_extras import sessions
import jinja2
from google.appengine.api import users
from jinja2.runtime import TemplateNotFound

from application import models, utils

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

JINJA_ENVIRONMENT.globals = {
    'utlis': utils
}


class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()

    def dispatch(self):
        try:
            super(BaseHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    @webapp2.cached_property
    def auth_config(self):
        """
              Dict to hold urls for login/logout
        """
        return {
            'login_url': users.create_login_url('/'),
            'logout_url': users.create_logout_url('/')
        }

    def render(self, template, **kwargs):
        kwargs.update({
            'singled_ind': True if users.get_current_user() else False,
            'upath_info': self.request.upath_info,
            'is_admin': True if users.is_current_user_admin() else False,
            'user': users.get_current_user()
        })

        kwargs.update(self.auth_config)

        try:
            template = JINJA_ENVIRONMENT.get_template(template)
            self.response.write(template.render(**kwargs))
        except TemplateNotFound:
            self.abort(404)


class UserHandler(BaseHandler):
    def dispatch(self):
        user = users.get_current_user()
        if user:
            try:
                self.user = user

                super(UserHandler, self).dispatch()
            finally:
                self.session_store.save_sessions(self.response)
        else:
            self.redirect(users.create_login_url(self.request.url))


class POCUserHandler(BaseHandler):
    def dispatch(self):
        user = users.get_current_user()
        if user:
            try:
                self.user = user

                poc_can_go = models.POCAccount.query(models.POCAccount.email == user.email()).fetch()
                if not users.is_current_user_admin():
                    if not poc_can_go:
                        self.abort(403)

                super(POCUserHandler, self).dispatch()
            finally:
                self.session_store.save_sessions(self.response)
        else:
            self.redirect(users.create_login_url(self.request.url))