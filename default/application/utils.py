__author__ = 'cage'

import math
import inspect
import json
import datetime
import logging

from google.appengine import runtime
from google.appengine.api.taskqueue import taskqueue


def each_hour_sending_rate(number_of_day, ip_count):
  base_quota = 1000 * ip_count
  quota = [0] * 24

  hourly_quota = int(math.pow(2, number_of_day) * base_quota)
  avarage = hourly_quota / 24
  for index, _ in enumerate(quota):

    if index == 0:
      quota[index] = avarage + int(math.fabs(avarage * 24 - hourly_quota))
    else:
      quota[index] = avarage

  return quota


def ipwarmup_day_sending_rate(number_of_day, ip_count):
  if number_of_day == 1:
    return each_hour_sending_rate(number_of_day, ip_count)
  else:
    resp = ipwarmup_day_sending_rate(number_of_day - 1, ip_count) + each_hour_sending_rate(number_of_day, ip_count)
    return resp


DATETIME_FORMAT = u'%Y-%m-%d %H:%M:%S'
DATE_FORMAT = u'%Y-%m-%d'
VALID_DATETIME_FORMATS = ('%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S')
## JSON
def to_json_encodable(data):
  """Converts data into json-compatible data."""
  if isinstance(data, unicode) or data is None:
    return data
  if isinstance(data, str):
    return data.decode('utf-8')
  if isinstance(data, (int, float, long)):
    # Note: overflowing is an issue with int and long.
    return data
  if isinstance(data, (list, set, tuple)):
    return [to_json_encodable(i) for i in data]
  if isinstance(data, dict):
    assert all(isinstance(k, basestring) for k in data), data
    return {
      to_json_encodable(k): to_json_encodable(v) for k, v in data.iteritems()
      }
  if isinstance(data, datetime.datetime):
    # Convert datetime objects into a string, stripping off milliseconds. Only
    # accept naive objects.
    if data.tzinfo is not None:
      raise ValueError('Can only serialize naive datetime instance')
    return data.strftime(DATETIME_FORMAT)
  if isinstance(data, datetime.date):
    return data.strftime(DATE_FORMAT)
  if isinstance(data, datetime.timedelta):
    # Convert timedelta into seconds, stripping off milliseconds.
    return int(data.total_seconds())
  if hasattr(data, 'to_dict') and callable(data.to_dict):
    # This takes care of ndb.Model.
    return to_json_encodable(data.to_dict())
  if hasattr(data, 'urlsafe') and callable(data.urlsafe):
    # This takes care of ndb.Key.
    return to_json_encodable(data.urlsafe())
  if inspect.isgenerator(data) or isinstance(data, xrange):
    # Handle it like a list. Sadly, xrange is not a proper generator so it has
    # to be checked manually.
    return [to_json_encodable(i) for i in data]
  assert False, 'Don\'t know how to handle %r' % data


def encode_to_json(data):
  """Converts any data as a json string."""
  return json.dumps(
    to_json_encodable(data),
    sort_keys=True,
    separators=(',', ':'),
    encoding='utf-8')

def enqueue_task(url, queue_name, params=None, payload=None, name=None, transactional=False):
  """Adds a task to a task queue.
  Returns True if a task was successfully added, logs error and returns False
  if task queue is acting up.
  https://chromium.googlesource.com/external/github.com/luci/luci-py/+/refs/heads/stable/appengine/components/components/utils.py
  """
  try:
    headers = None
    # Note that just using 'target=module' here would redirect task request to
    # a default version of a module, not the currently executing one.
    taskqueue.add(
      url=url,
      queue_name=queue_name,
      payload=payload,
      params=params,
      name=name,
      headers=headers,
      transactional=transactional)
    return True
  except (
      taskqueue.Error,
      runtime.DeadlineExceededError,
      runtime.apiproxy_errors.CancelledError,
      runtime.apiproxy_errors.DeadlineExceededError,
      runtime.apiproxy_errors.OverQuotaError) as e:
    logging.warning(
      'Problem adding task \'%s\' to task queue \'%s\' (%s): %s',
      url, queue_name, e.__class__.__name__, e)
    return False