__author__ = 'cage'

import logging
import time
import itertools

from google.appengine import runtime
from google.appengine.api.taskqueue import taskqueue

from models import FlexWebhook


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


def timeit(function):
  def _decorated(self, *args, **kwargs):
    self.ts = time.time()
    return function(self, *args, **kwargs)

  return _decorated


class Wrap:
  def __init__(self, val):
    self.val = val

  def unlink(self):
    val = self.val
    self.val = None
    return val


def grouper(iterable, chunksize):
  i = iter(iterable)
  while True:
    chunk = Wrap(list(itertools.islice(i, int(chunksize))))
    if not chunk.val:
      break
    yield chunk.unlink()