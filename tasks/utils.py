__author__ = 'cage'

import time
import math
import calendar
from datetime import datetime, timedelta


def each_hour_sending_rate(number_of_day, ip_count, HOW_MANY_HOURS_DO_THE_JOB):
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
  daily_quota = 1000 * ip_count
  quota = [0] * 24

  hourly_quota = int(math.pow(2, number_of_day) * daily_quota)

  avarage = hourly_quota / HOW_MANY_HOURS_DO_THE_JOB
  for index, _ in enumerate(quota):

    if index < HOW_MANY_HOURS_DO_THE_JOB:
      if index == 0:
        quota[index] = avarage + int(math.fabs(avarage * HOW_MANY_HOURS_DO_THE_JOB - hourly_quota))

      else:
        quota[index] = avarage

  return quota


def ipwarmup_day_sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB=24):
  """

  :param days:
  :param ip_count:
  :param HOW_MANY_HOURS_DO_THE_JOB:
  :return:
  """

  if HOW_MANY_HOURS_DO_THE_JOB > 24:
    HOW_MANY_HOURS_DO_THE_JOB = 24

  if days == 1:
    return each_hour_sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB)

  else:
    resp = ipwarmup_day_sending_rate(days - 1, ip_count, HOW_MANY_HOURS_DO_THE_JOB) + each_hour_sending_rate(days,
                                                                                                             ip_count,
                                                                                                             HOW_MANY_HOURS_DO_THE_JOB)
    return resp