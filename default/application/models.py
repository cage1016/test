from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import User

from application import blob_files


__author__ = 'cage'


class User(User):
    """
    Universal user model. Can be used with App Engine's default users API,
    own auth or third party authentication methods (OpenID, OAuth etc).
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #: User defined unique name, also used as key_name.
    # Not used by OpenID
    username = ndb.StringProperty()
    #: User Name
    name = ndb.StringProperty()
    #: User Last Name
    last_name = ndb.StringProperty()
    #: User email
    email = ndb.StringProperty()

    @classmethod
    def get_by_email(cls, email):
        """Returns a user object based on an email.

        :param email:
            String representing the user email. Examples:

        :returns:
            A user object.
        """
        return cls.query(cls.email == email).get()


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