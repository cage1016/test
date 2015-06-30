# coding=utf-8

from google.appengine.ext import ndb
import general_counter

# should same as default/models.py
class RecipientData(ndb.Expando):
  pass


# should same as default/models.py
class RecipientQueueData(ndb.Model):
  schedule_key = ndb.KeyProperty(kind='Schedule', required=True)
  data = ndb.JsonProperty(compressed=True)
  status = ndb.StringProperty(default='')
  created = ndb.DateTimeProperty(auto_now_add=True)


# should same as default/models.py
# updated 2015/5/21
class Schedule(ndb.Model):
  sendgrid_account = ndb.StringProperty()
  category = ndb.StringProperty()
  reply_to = ndb.StringProperty()

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
  # target
  hour_target_capacity = ndb.IntegerProperty(default=0)
  # invalid email
  invalid_email = ndb.IntegerProperty(default=0)
  # 預設是將每天的量分成24小時間來發，
  # default: 1/24hrs, 如果前5個小時要發完 1/5hrs
  hour_rate = ndb.StringProperty()

  # timestamp: query property for cron job
  schedule_timestamp = ndb.FloatProperty()
  # schedule display for human
  schedule_display = ndb.DateTimeProperty()
  # schedule has been executed
  # schedule_executed = ndb.BooleanProperty(default=False)
  # schedule_finished = ndb.BooleanProperty(default=False)

  txt_object_name = ndb.StringProperty()
  edm_object_name = ndb.StringProperty()
  replace_edm_csv_property = ndb.StringProperty()

  recipientQueue = ndb.KeyProperty(kind=RecipientQueueData, repeated=True)
  error = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)

  # delete status
  # when start to delete schedule
  # it will set to 'procress'
  # and detete itself when cron
  # job check other relative entities
  # has been deleted
  status = ndb.StringProperty(default='')
  success_worker = ndb.IntegerProperty(default=0)
  fail_worker = ndb.IntegerProperty(default=0)

  # sharding counter name
  sharding_count_name = ndb.StringProperty()

  # delete mark
  delete_mark_RecipientQueueData = ndb.BooleanProperty(default=False)
  delete_mark_logEmail = ndb.BooleanProperty(default=False)
  delete_mark_LogFailEmail = ndb.BooleanProperty(default=False)
  delete_mark_ReTry = ndb.BooleanProperty(default=False)


class LogEmail(ndb.Model):
  schedule_key = ndb.KeyProperty(kind='Schedule', required=True)
  # 真正的 sender: 'sendgrid' or google service account
  sender = ndb.StringProperty(required=True)
  category = ndb.StringProperty()

  sender_name = ndb.StringProperty()
  sender_email = ndb.StringProperty()

  to = ndb.StringProperty(required=True)
  subject = ndb.StringProperty(required=True)
  body = ndb.TextProperty()
  reply_to = ndb.StringProperty()

  # inherit from schedule
  schedule_timestamp = ndb.FloatProperty()
  schedule_display = ndb.DateTimeProperty()

  when_timestamp = ndb.FloatProperty()
  when_display = ndb.DateTimeProperty()

  created = ndb.DateTimeProperty(auto_now_add=True)
  sendgrid_account = ndb.StringProperty()
  fails_link = ndb.KeyProperty(kind='LogFailEmail', repeated=True)


class LogFailEmail(LogEmail):
  reason = ndb.StringProperty(required=True)

  def _post_put_hook(self, future):
    """
    assign failemail to try and keep logFailEmail
    :param future:
    """

    self_key = future.get_result()

    @ndb.tasklet
    def update_changed(self_key, schedule_key):
      reTry = ReTry()
      reTry.schedule_key = schedule_key
      reTry.failEmail = self_key
      yield reTry.put_async()

    ndb.Future.wait_all([
      update_changed(self_key, self.schedule_key)
    ])


class ReTry(ndb.Model):
  schedule_key = ndb.KeyProperty(kind='Schedule', required=True)
  failEmail = ndb.KeyProperty(kind='LogFailEmail', required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)


class InvalidEmails(ndb.Model):
  schedule_key = ndb.KeyProperty(kind='Schedule', required=True)
  sendgrid_account = ndb.StringProperty()
  category = ndb.StringProperty()
  schedule_subject = ndb.StringProperty()
  schedule_display = ndb.DateTimeProperty()
  email = ndb.StringProperty()
  hour_rate = ndb.StringProperty()
  gi = ndb.IntegerProperty(default=0)
  hr = ndb.IntegerProperty(default=0)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def new(cls, schedule_key, row):
    invalid_email = InvalidEmails()
    invalid_email.schedule_key = schedule_key
    invalid_email.sendgrid_account = row.get('sendgrid_account')
    invalid_email.category = row.get('category')
    invalid_email.schedule_subject = row.get('schedule_subject')
    invalid_email.schedule_display = row.get('schedule_display')
    invalid_email.email = row.get('email')
    invalid_email.gi = int(row.get('gi'))
    invalid_email.hr = int(row.get('hr'))

    return invalid_email
