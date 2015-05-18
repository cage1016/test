__author__ = 'cage'

import time
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