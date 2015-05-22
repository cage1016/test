# coding=utf-8

from google.appengine.ext import ndb

# should same as default/models.py
class RecipientData(ndb.Expando):
  pass


# should same as default/models.py
class RecipientQueueData(ndb.Model):
  data = ndb.JsonProperty(compressed=True)
  created = ndb.DateTimeProperty(auto_now_add=True)


# should same as default/models.py
# updated 2015/5/21
class Schedule(ndb.Model):
  category = ndb.StringProperty()

  # ipwarmup, poc etc
  type = ndb.StringProperty()

  # 開始時間後第幾個小時. 1開始
  hour_delta = ndb.IntegerProperty()
  # 每個小時發的容量
  hour_capacity = ndb.IntegerProperty()
  # 預設是將每天的量分成24小時間來發，
  # default: 1/24hrs, 如果前5個小時要發完 1/5hrs
  hour_rate = ndb.StringProperty()

  # timestamp: query property for cron job
  schedule_timestamp = ndb.FloatProperty()
  # schedule display for human
  schedule_display = ndb.DateTimeProperty()

  txt_object_name = ndb.StringProperty()
  edm_object_name = ndb.StringProperty()

  recipientQueue = ndb.KeyProperty(kind=RecipientQueueData, repeated=True)
  created = ndb.DateTimeProperty(auto_now_add=True)


