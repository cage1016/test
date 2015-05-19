__author__ = 'cage'

import webapp2
import logging

from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from application.models import RecipientData

from application.controllers.base import ValidateGCSWithCredential

import itertools

CHUCKS_SIZE = 50


class RecipientDeleteHandler(webapp2.RequestHandler):
  def post(self):
    skey = self.request.get('skey')

    data_recipient = ndb.Key(urlsafe=skey).get()

    if data_recipient:

      cursor = None
      while True:
        curs = Cursor(urlsafe=cursor)
        recipients_data, next_curs, more = RecipientData.query(
          ancestor=data_recipient.key).fetch_page(CHUCKS_SIZE, start_cursor=curs)

        ndb.delete_multi([m.key for m in recipients_data])

        if more and next_curs:
          cursor = next_curs.urlsafe()

        else:
          break

      data_recipient.key.delete()


class RecipientQueueDataDeleteHandler(webapp2.RequestHandler):
  def worker(self, chunk):
    return chunk[0]

  def post(self):
    skey = self.request.get('skey')

    data_sendemail = ndb.Key(urlsafe=skey).get()

    num_chunks = 20

    chunks = itertools.groupby(data_sendemail.recipients)
    while True:
      # make a list of num_chunks chunks
      groups = [list(chunk) for key, chunk in
                itertools.islice(chunks, num_chunks)]
      if groups:
        ndb.delete_multi(map(self.worker, groups))
      else:
        break

    data_sendemail.key.delete()


class RecipientTxtDeleteHandler(webapp2.RequestHandler):
  @ValidateGCSWithCredential
  def post(self):
    object_name = self.request.get('object_name')

    req = self.gcs_service.objects().delete(bucket=self.gcs_service.BUCKET, object=object_name)
    resp = req.execute()

    logging.info(resp)