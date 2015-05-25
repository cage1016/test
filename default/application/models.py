# coding=utf-8

__author__ = 'cage'

import datetime

from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models as auth_models

import application.settings as settings
from application.apis.resources_messages import ResourcesResponseMessage

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)


class AbstractNDBModel(ndb.Model):
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


class Resource(AbstractNDBModel):
  object_name = ndb.StringProperty()
  display_name = ndb.StringProperty()
  bucket = ndb.StringProperty()
  size = ndb.IntegerProperty()
  content_type = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)

  def to_response_message(self):
    rrm = ResourcesResponseMessage()
    rrm.object_name = self.object_name
    rrm.display_name = self.display_name
    rrm.bucket = self.bucket
    rrm.size = self.size
    rrm.content_type = self.content_type
    rrm.created = self.created.strftime('%Y-%m-%d %H:%M:%S')
    rrm.urlsafe = self.key.urlsafe()

    return rrm


class RecipientData(ndb.Expando):
  pass


# should same as default/models.py
class RecipientQueueData(ndb.Model):
  data = ndb.JsonProperty(compressed=True)
  created = ndb.DateTimeProperty(auto_now_add=True)


# should same as default/models.py
# updated 2015/5/21
class Schedule(AbstractNDBModel):
  category = ndb.StringProperty()

  # subject
  subject = ndb.StringProperty()
  sender_name = ndb.StringProperty()
  sender_email = ndb.StringProperty()

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
