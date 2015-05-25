__author__ = 'cage'

import endpoints
from protorpc import messages
from protorpc import message_types


class SchedulesListRequest(messages.Message):
  pass


class SchedulesResponseMessage(messages.Message):
  urlsafe = messages.StringField(1)
  subject = messages.StringField(2)
  category = messages.StringField(3)
  schedule_display = messages.StringField(4)
  hour_capacity = messages.IntegerField(5)
  hour_delta = messages.IntegerField(6)
  hour_rate = messages.StringField(7)
  edm_object_name = messages.StringField(8)
  txt_object_name = messages.StringField(9)
  created = messages.StringField(10)


class SchedulesListResponse(messages.Message):
  pre_cursor = messages.StringField(1)
  next_cursor = messages.StringField(2)
  data = messages.MessageField(SchedulesResponseMessage, 3, repeated=True)


SCHEDULES_LIST_RESOURCE = endpoints.ResourceContainer(
  SchedulesListRequest,
  p=messages.StringField(2),
  c=messages.StringField(3),
  per_page=messages.IntegerField(4))
