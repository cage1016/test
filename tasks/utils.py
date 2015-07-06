__author__ = 'cage'

from delorean import Delorean, parse
import math
import datetime
import logging
import re
import time
import decimal
import random

from google.appengine import runtime
from google.appengine.api.taskqueue import taskqueue

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def time_to_utc(my_time):
  d = parse(my_time)
  d = d.datetime + datetime.timedelta(hours=-8)
  d = parse(d.strftime(TIME_FORMAT))
  return d.truncate('minute')


def time_add(d, delta):
  _d = d.datetime + datetime.timedelta(hours=delta)
  return parse(_d.strftime(TIME_FORMAT))


def hourly_sending_rate(number_of_day, ip_count, HOW_MANY_HOURS_DO_THE_JOB, DAILY_CAPACITY):
  """
  utils func - each_hour_sending_rate()
  how many ip warmup email we can send by sendgrid suggest schedule per hours

  number_of_day
  ip_count
  HOW_MANY_HOURS_DO_THE_JOB

  Args:
    ipwarmup_day_sending_rate(1,1)

  [91, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83]

  """
  daily_quota = DAILY_CAPACITY * ip_count
  quota = [0] * 24

  hourly_quota = int(math.pow(2, number_of_day) * daily_quota)

  avarage = hourly_quota / HOW_MANY_HOURS_DO_THE_JOB
  for index, _ in enumerate(quota):

    if index < HOW_MANY_HOURS_DO_THE_JOB:
      if index == 0:
        quota[index] = avarage + \
                       int(math.fabs(
                         avarage * HOW_MANY_HOURS_DO_THE_JOB - hourly_quota))

      else:
        quota[index] = avarage

  return quota


def daily_sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB=24, DAILY_CAPACITY=1000):
  """

  :param days:
  :param ip_count:
  :param HOW_MANY_HOURS_DO_THE_JOB:
  :return:
  """

  if HOW_MANY_HOURS_DO_THE_JOB > 24:
    HOW_MANY_HOURS_DO_THE_JOB = 24

  if days == 1:
    return hourly_sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB, DAILY_CAPACITY)

  else:
    resp = daily_sending_rate(days - 1,
                              ip_count,
                              HOW_MANY_HOURS_DO_THE_JOB,
                              DAILY_CAPACITY) + hourly_sending_rate(days,
                                                                    ip_count,
                                                                    HOW_MANY_HOURS_DO_THE_JOB,
                                                                    DAILY_CAPACITY)
    return resp


def sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB=24, DAILY_CAPACITY=1000):
  rate = daily_sending_rate(
    days, ip_count, HOW_MANY_HOURS_DO_THE_JOB, DAILY_CAPACITY)

  return rate, sum(rate)


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


def replace_edm_csv_property(content, user_data, targets):
  """
  replace html content by user defind property with user data

  :param content: html content
  :param user_data: {"gi": 90, "ii": 90, "hr": 0, "email": "xxx@kimo.com", "cmem_num": "1263175"}
  :param targets: the html keyword want to replace by user_data. <?pid?>:cmem_num,<?sd_id?>:pid ex
  :return: replaced html content
  """

  if not targets:
    return content

  # replace user defined keyword by user_data
  # '<?pid?>:cmem_num,<?sd_id?>:pid' ==> {'<?pid?>': 'cmem_num', '<?sd_id?>': 'pid'}
  for key, value in dict([s.split(':') for s in targets.split(',')]).items():
    if not user_data.__contains__(value):
      continue

    content = re.sub(re.escape(key), str(user_data.get(value)), content)

  return content


def timeit(function):
  def _decorated(self, *args, **kwargs):
    self.ts = time.time()
    return function(self, *args, **kwargs)

  return _decorated


def true_false_pick(false_rate=0.5):
  exponent = decimal.Decimal(str(false_rate)).as_tuple().exponent
  t = int(1 / pow(10, exponent))

  number_of_false = int(t * false_rate)
  number_of_true = t - number_of_false
  return random.choice([True] * number_of_true + [False] * number_of_false)
