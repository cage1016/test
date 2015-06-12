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
  schedule_executed = ndb.BooleanProperty(default=False)

  txt_object_name = ndb.StringProperty()
  edm_object_name = ndb.StringProperty()
  replace_edm_csv_property = ndb.StringProperty()

  recipientQueue = ndb.KeyProperty(kind=RecipientQueueData, repeated=True)
  error = ndb.StringProperty()
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

    @ndb.transactional_tasklet
    def update_changed(self_key):
      schedule_key = self_key.parent()
      reTry = ReTry(parent=schedule_key)
      reTry.failEmail = self_key

      yield ndb.put_multi_async([reTry])

    ndb.Future.wait_all([
      update_changed(self_key)
    ])


class ReTry(ndb.Model):
  failEmail = ndb.KeyProperty(kind='LogFailEmail', required=True)


class InvalidEmails(ndb.Model):
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
  def new(cls, ancestor_key, row):
    invalid_email = InvalidEmails(parent=ancestor_key)
    invalid_email.sendgrid_account = row.get('sendgrid_account')
    invalid_email.category = row.get('category')
    invalid_email.schedule_subject = row.get('schedule_subject')
    invalid_email.schedule_display = row.get('schedule_display')
    invalid_email.email = row.get('email')
    invalid_email.gi = int(row.get('gi'))
    invalid_email.hr = int(row.get('hr'))

    return invalid_email
