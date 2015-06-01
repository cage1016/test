# coding=utf-8

from google.appengine.ext import ndb

# should same as default/models.py
class RecipientData(ndb.Expando):
  pass


# should same as default/models.py
class RecipientQueueData(ndb.Model):
  data = ndb.JsonProperty(compressed=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  @ndb.tasklet
  def delete_all_for_schedule(cls, schedule_key):
    yield ndb.delete_multi_async(cls.query(ancestor=schedule_key).fetch(keys_only=True, batch_size=100))


# should same as default/models.py
# updated 2015/5/21
class Schedule(ndb.Model):
  sendgrid_account = ndb.StringProperty()
  category = ndb.StringProperty()

  # subject
  subject = ndb.StringProperty()
  sender_name = ndb.StringProperty()
  sender_email = ndb.StringProperty()

  # ipwarmup, poc etc
  type = ndb.StringProperty()

  # 開始時間後第幾個小時. 1開始
  hour_delta = ndb.IntegerProperty(default=0)
  # 每個小時發的容量
  hour_capacity = ndb.IntegerProperty(default=0)
  # 預設是將每天的量分成24小時間來發，
  # default: 1/24hrs, 如果前5個小時要發完 1/5hrs
  hour_rate = ndb.StringProperty()

  # timestamp: query property for cron job
  schedule_timestamp = ndb.FloatProperty()
  # schedule display for human
  schedule_display = ndb.DateTimeProperty()
  # schedule has been executed
  schedule_executed = ndb.BooleanProperty(default=False)

  txt_object_name = ndb.StringProperty()
  edm_object_name = ndb.StringProperty()

  recipientQueue = ndb.KeyProperty(kind=RecipientQueueData, repeated=True)
  created = ndb.DateTimeProperty(auto_now_add=True)


class LogEmail(ndb.Model):
  # 真正的 sender: 'sendgrid' or google service account
  sender = ndb.StringProperty(required=True)
  category = ndb.StringProperty()

  sender_name = ndb.StringProperty()
  sender_email = ndb.StringProperty()

  to = ndb.StringProperty(required=True)
  subject = ndb.StringProperty(required=True)
  body = ndb.TextProperty()

  # inherit from schedule
  schedule_timestamp = ndb.FloatProperty()
  schedule_display = ndb.DateTimeProperty()

  when_timestamp = ndb.FloatProperty()
  when_display = ndb.DateTimeProperty()

  created = ndb.DateTimeProperty(auto_now_add=True)

  def get_id(self):
    return self._key.id()


class LogSendEmailFail(LogEmail):
  reason = ndb.StringProperty(required=True)

  def get_id(self):
    return self._key.id()
