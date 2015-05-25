__author__ = 'cage'

import endpoints
from protorpc import messages
from protorpc import message_types


class ResourcesListRequest(messages.Message):
  pass


class ResourcesInsertRequest(messages.Message):
  id = messages.StringField(1)
  name = messages.StringField(2)
  bucket = messages.StringField(3)
  size = messages.StringField(4)
  contentType = messages.StringField(5)


class ResourcesDeleteRequest(messages.Message):
  pass


class ResourcesResponseMessage(messages.Message):
  object_name = messages.StringField(1)
  display_name = messages.StringField(2)
  bucket = messages.StringField(3)
  size = messages.IntegerField(4)
  content_type = messages.StringField(5)
  created = messages.StringField(6)
  urlsafe = messages.StringField(7)


class ResourcesDeleteResponse(messages.Message):
  urlsafe = messages.StringField(1)


class ResourcesListResponse(messages.Message):
  pre_cursor = messages.StringField(1)
  next_cursor = messages.StringField(2)
  data = messages.MessageField(ResourcesResponseMessage, 3, repeated=True)


RESOURCES_LIST_RESOURCE = endpoints.ResourceContainer(
  ResourcesListRequest,
  p=messages.StringField(2),
  c=messages.StringField(3),
  per_page=messages.IntegerField(4))

RESOURCES_INSERT_RESOURCE = endpoints.ResourceContainer(
  ResourcesInsertRequest)

RESOURCES_DELETE_RESOURCE = endpoints.ResourceContainer(
  ResourcesDeleteRequest,
  id=messages.StringField(2, required=True))