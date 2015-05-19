__author__ = 'cage'

import datetime

from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models as auth_models

from application import blob_files
import application.settings as settings


class User(auth_models.User):
  account_enabled = ndb.BooleanProperty(default=False)
  report_enabled = ndb.BooleanProperty(default=False)
  description = ndb.TextProperty(default='')


SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)


class RecipientTxt(ndb.Model):
  object_name = ndb.StringProperty()
  display_name = ndb.StringProperty()
  bucket = ndb.StringProperty()
  size = ndb.IntegerProperty()
  content_type = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)

  def to_dict(self):
    output = {}

    for key, prop in self._properties.iteritems():
      value = getattr(self, key)

      if value is None or isinstance(value, SIMPLE_TYPES):
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
      else:
        raise ValueError('cannot encode ' + repr(prop))

    output['urlsafe'] = self.key.urlsafe()
    return output


class IPWarmup(ndb.Model):
  count = ndb.IntegerProperty(default=0)
  email = ndb.StringProperty()


class RecipientQueueData(ndb.Model):
  """
  ex json:{
      email: xxx@gmail.com
      name: cage.chung
      type: to/cc/bcc
  }
  """
  data = ndb.JsonProperty(compressed=True)
  created = ndb.DateTimeProperty(auto_now_add=True)


class RecipientData(ndb.Expando):
  pass


class Recipient(ndb.Model):
  name = ndb.StringProperty(required=True, default='')
  count = ndb.IntegerProperty(required=True, default=0)
  created = ndb.DateTimeProperty(auto_now_add=True)
  status = ndb.StringProperty()

  @classmethod
  def query_recipient(cls, ancestor_key):
    return cls.query(ancestor=ancestor_key).order(-cls.created)


class ScheduleEmail(ndb.Model):
  created = ndb.DateTimeProperty(auto_now_add=True)
  subject = ndb.StringProperty()
  toname = ndb.StringProperty()
  toemail = ndb.StringProperty()
  category = ndb.StringProperty()
  schedule = ndb.FloatProperty()
  recipients_name = ndb.StringProperty()
  recipients_count = ndb.IntegerProperty(default=0)
  recipients = ndb.KeyProperty(kind=RecipientQueueData, repeated=True)
  template = ndb.KeyProperty(kind=blob_files.BlobFiles)
  template_name = ndb.StringProperty()
  status = ndb.StringProperty(default='')
  success_count = ndb.IntegerProperty(default=0)
  error_count = ndb.IntegerProperty(default=0)


  @classmethod
  def query_sendmail(cls, ancestor_key):
    return cls.query(ancestor=ancestor_key).order(-cls.created)


class LogEmail(ndb.Model):
  sender = ndb.StringProperty(required=True)
  category = ndb.StringProperty()
  toname = ndb.StringProperty()
  toemail = ndb.StringProperty()
  to = ndb.StringProperty(required=True)
  subject = ndb.StringProperty(required=True)
  body = ndb.TextProperty()
  schedule = ndb.FloatProperty()
  when = ndb.DateTimeProperty()

  def get_id(self):
    return self._key.id()


class LogSendEmailFail(ndb.Model):
  sender = ndb.StringProperty(required=True)
  category = ndb.StringProperty()
  toname = ndb.StringProperty()
  toemail = ndb.StringProperty()
  to = ndb.StringProperty(required=True)
  subject = ndb.StringProperty(required=True)
  body = ndb.TextProperty()
  schedule = ndb.FloatProperty()
  when = ndb.DateTimeProperty()
  reason = ndb.StringProperty(required=True)

  def get_id(self):
    return self._key.id()


class POCAccount(ndb.Model):
  email = ndb.StringProperty()


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