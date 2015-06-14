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
  schedule_executed = messages.BooleanField(11)
  sendgrid_account = messages.StringField(12)
  replace_edm_csv_property = messages.StringField(13)
  invalid_email = messages.IntegerField(14)
  error = messages.StringField(15)


class SchedulesListResponse(messages.Message):
  pre_cursor = messages.StringField(1)
  next_cursor = messages.StringField(2)
  data = messages.MessageField(SchedulesResponseMessage, 3, repeated=True)


class SchedulesDeleteRequest(messages.Message):
  pass


class SchedulesDeleteResponse(messages.Message):
  urlsafe = messages.StringField(1)


class SchedulesInsertRequest(messages.Message):
  recipientTxtUrlsafe = messages.StringField(1)
  recipientEdmUrlsafe = messages.StringField(2)
  subject = messages.StringField(3)
  senderName = messages.StringField(4)
  senderEmail = messages.StringField(5)
  type = messages.StringField(6)
  scheduleDuration = messages.IntegerField(7)
  ipCounts = messages.IntegerField(8)
  dailyCapacity = messages.IntegerField(9)
  category = messages.StringField(10)
  recipientSkip = messages.IntegerField(11)
  startTime = messages.StringField(12)
  hourRate = messages.IntegerField(13)
  sendgridAccount = messages.StringField(14)
  replyTo = messages.StringField(15)
  replaceEdmCSVProperty = messages.StringField(16)


class SchedulesInsertResponse(messages.Message):
  msg = messages.StringField(1)


SCHEDULES_LIST_RESOURCE = endpoints.ResourceContainer(
  SchedulesListRequest,
  p=messages.StringField(2),
  c=messages.StringField(3),
  per_page=messages.IntegerField(4),
  categories=messages.StringField(5))

SCHEDULES_INSERT_RESOURCE = endpoints.ResourceContainer(
  SchedulesInsertRequest)

SCHEDULES_DELETE_RESOURCE = endpoints.ResourceContainer(
  SchedulesDeleteRequest,
  id=messages.StringField(2, required=True))
