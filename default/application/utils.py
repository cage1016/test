__author__ = 'cage'

import time
import math
import calendar
from datetime import datetime, timedelta


def get_date_time(format="%Y-%m-%d %H:%M:%S", UTC_OFFSET=8):
  """
  Get date and time in UTC with a specific format
   By default it UTC = -3 (Chilean Time)
  """

  local_datetime = datetime.now()
  now = local_datetime + timedelta(hours=UTC_OFFSET)
  if format != "datetimeProperty":
    now = now.strftime(format)
    # now = datetime.fromtimestamp(1321925140.78)
  return now


def get_timestampe(datetime):
  return calendar.timegm(datetime.timetuple())


def get_datetime(timestamp):
  return datetime.utcfromtimestamp(timestamp)


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