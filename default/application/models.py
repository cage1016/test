# coding=utf-8

__author__ = 'cage'

import datetime

from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models as auth_models

import application.settings as settings
from application import general_counter

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)


class temporary(ndb.Model):
  pass

  def _to_dict(self, include=None, exclude=None):
    output = {}

    for key, prop in self._properties.iteritems():
      value = getattr(self, key)

      if value is None or isinstance(value, SIMPLE_TYPES):
        if isinstance(value, list):
          if isinstance(value[0], ndb.Key):
            output[key] = [v.urlsafe() for v in value]
          else:
            output[key] = value
        else:
          output[key] = value
      elif isinstance(value, datetime.date):
        # Convert date/datetime to MILLISECONDS-since-epoch (JS "new Date()").
        # ms = time.mktime(value.utctimetuple()) * 1000
        # ms += getattr(value, 'microseconds', 0) / 1000
        # output[key] = int(ms)
        output[key] = value.strftime('%Y-%m-%d %H:%M:%S')
      elif isinstance(value, ndb.GeoPt):
        output[key] = {'lat': value.lat, 'lon': value.lon}
      elif isinstance(value, ndb.Model):
        output[key] = self.to_dict(value)
      elif isinstance(value, ndb.KeyProperty):
        output[key] = self.to_dict(value)
      else:
        raise ValueError('cannot encode ' + repr(prop))

    output['urlsafe'] = self.key.urlsafe()
    return output


class User(auth_models.User):
  account_enabled = ndb.BooleanProperty(default=False)
  report_enabled = ndb.BooleanProperty(default=False)
  description = ndb.TextProperty(default='')


class Resource(ndb.Model):
  object_name = ndb.StringProperty()
  display_name = ndb.StringProperty()
  bucket = ndb.StringProperty()
  size = ndb.IntegerProperty()
  content_type = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def query_by_page(cls, cursor, forward, per_page, **params):

    if forward:
      query = cls.query().order(-cls.created, -cls._key)
      data, next_cursor, more = query.fetch_page(per_page, start_cursor=cursor)

      if next_cursor and more:
        next_cursor = next_cursor.urlsafe()
        params.update(next_cursor=next_cursor)

      if cursor:
        pre_cursor = cursor.reversed().urlsafe()
        params.update(pre_cursor=pre_cursor)

    else:
      query = cls.query().order(cls.created, cls._key)
      data, next_cursor, more = query.fetch_page(per_page, start_cursor=cursor)

      if next_cursor and more:
        pre_cursor = next_cursor.urlsafe()
        params.update(pre_cursor=pre_cursor)

      next_cursor = cursor.reversed().urlsafe()
      params.update(next_cursor=next_cursor)

    params.update(data=data)

    return params


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

  # dump, gcs download path
  unsend_recipients_log = ndb.StringProperty(default='')
  send_recipients_log = ndb.StringProperty(default='')

  # for test
  is_dry_run = ndb.BooleanProperty(default=False)
  dry_run_fail_rate = ndb.FloatProperty(default=0.0)

  def get_tasks_executed_count(self):
    if self.sharding_count_name:
      return general_counter.get_count(self.sharding_count_name)

    else:
      return 0

  @classmethod
  def query_by_page(cls, categories, cursor, forward, per_page, **params):
    query = cls.query()
    if forward:
      if categories:
        query = query.filter(cls.category.IN(categories.split(',')))

      query = query.order(-cls.created, -cls._key)
      data, next_cursor, more = query.fetch_page(per_page, start_cursor=cursor)

      if next_cursor and more:
        next_cursor = next_cursor.urlsafe()
        params.update(next_cursor=next_cursor)

      if cursor:
        pre_cursor = cursor.reversed().urlsafe()
        params.update(pre_cursor=pre_cursor)

    else:
      if categories:
        query = query.filter(cls.category.IN(categories.split(',')))

      query = query.order(cls.created, cls._key)
      data, next_cursor, more = query.fetch_page(per_page, start_cursor=cursor)

      if next_cursor and more:
        pre_cursor = next_cursor.urlsafe()
        params.update(pre_cursor=pre_cursor)

      next_cursor = cursor.reversed().urlsafe()
      params.update(next_cursor=next_cursor)

    params.update(data=data)

    return params


class Site(ndb.Model):
  VERSION = 1
  baseurl = ndb.StringProperty(default=None)
  name = ndb.StringProperty()
  article_per_page = ndb.IntegerProperty()
  admin_article_per_page = ndb.IntegerProperty()
  feed_url = ndb.StringProperty()
  disqus_shortname = ndb.StringProperty()


def InitSiteDate():
  global g_site

  # Site
  g_site = Site(id='default')
  g_site.baseurl = settings.BASIC_SITE_URL
  g_site.name = settings.SITE_NAME
  g_site.disqus_shortname = settings.DISQUS_SHORTNAME

  g_site.put()

  return g_site


def global_init(forceUpdate=False):
  global g_site
  try:
    if g_site:
      return g_site

  except:
    pass

  g_site = Site.get_by_id('default')
  if not g_site or forceUpdate:
    g_site = InitSiteDate()

  return g_site


try:
  g_site = global_init(forceUpdate=True)

except:
  pass
