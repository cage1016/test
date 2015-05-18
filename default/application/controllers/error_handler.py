__author__ = 'cage'

from application.controllers.basehandler import BaseHandler


class Handle403(BaseHandler):
    def get(self):
        self.render("403.html")


class Handle404(BaseHandler):
    def get(self):
        self.render("404.html")


class Handle500(BaseHandler):
    def get(self):
        self.render("500.html")