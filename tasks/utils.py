__author__ = 'cage'

from delorean import Delorean, parse
import math
import datetime


def time_to_utc(my_time):
  d = parse(my_time)
  d = d.datetime + datetime.timedelta(hours=-8)
  d = parse(d.strftime('%Y-%m-%d %H:%M:%S'))
  return d.truncate('minute')


def each_hour_sending_rate(number_of_day, ip_count, HOW_MANY_HOURS_DO_THE_JOB, DAILY_CAPACITY):
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
        quota[index] = avarage + int(math.fabs(avarage * HOW_MANY_HOURS_DO_THE_JOB - hourly_quota))

      else:
        quota[index] = avarage

  return quota


def ipwarmup_day_sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB=24, DAILY_CAPACITY=1000):
  """

  :param days:
  :param ip_count:
  :param HOW_MANY_HOURS_DO_THE_JOB:
  :return:
  """

  if HOW_MANY_HOURS_DO_THE_JOB > 24:
    HOW_MANY_HOURS_DO_THE_JOB = 24

  if days == 1:
    return each_hour_sending_rate(days, ip_count, HOW_MANY_HOURS_DO_THE_JOB, DAILY_CAPACITY)

  else:
    resp = ipwarmup_day_sending_rate(days - 1,
                                     ip_count,
                                     HOW_MANY_HOURS_DO_THE_JOB,
                                     DAILY_CAPACITY) + each_hour_sending_rate(days,
                                                                              ip_count,
                                                                              HOW_MANY_HOURS_DO_THE_JOB,
                                                                              DAILY_CAPACITY)
    return resp