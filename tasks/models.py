from google.appengine.ext import ndb

# should same as default/models.py
class RecipientData(ndb.Expando):
  pass


# should same as default/models.py
# updated 2015/5/21
class IpWarmupSchedule(ndb.Model):
  category = ndb.StringProperty()
  index_of_hour = ndb.IntegerProperty()
  schedule = ndb.FloatProperty()  # time
  display_schedule = ndb.DateTimeProperty()
  number_of_sending_mail = ndb.IntegerProperty()
  txt_object_name = ndb.StringProperty()
  edm_object_name = ndb.StringProperty()
  how_many_hours_do_the_job = ndb.IntegerProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)