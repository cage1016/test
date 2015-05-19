__author__ = 'cage'

import endpoints
from protorpc import messages
from protorpc import message_types


class RecipientInsertRequest(messages.Message):
  body = messages.BytesField(1)
  file_name = messages.StringField(2)
  content_type = messages.StringField(3)


class RecipientInsertResponse(messages.Message):
  id = messages.StringField(1)
  name = messages.StringField(2)
  bucket = messages.StringField(3)


RECIPIENT_INSERT_RESOURCE = endpoints.ResourceContainer(
  RecipientInsertRequest)