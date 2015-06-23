from google.appengine.ext import ndb
from google.appengine.ext.db import Timeout
from google.appengine import runtime

import tasks

### Private stuff.
def _process_chunk_of_items(
    map_fn, action_futures, items_to_process, max_inflight, map_page_size):
  """Maps as many items as possible and throttles down to 'max_inflight'.
  |action_futures| is modified in-place.
  Remaining items_to_process is returned.
  """
  # First, throttle.
  pop_future_done(action_futures)
  while len(action_futures) > max_inflight:
    ndb.Future.wait_any(action_futures)
    pop_future_done(action_futures)
  # Then, map. map_fn() may return None so "or []" to not throw an exception. It
  # just means there no async operation to wait on.
  action_futures.extend(map_fn(items_to_process[:map_page_size]) or [])
  return items_to_process[map_page_size:]
  ### Public API.


### Public API.
def pop_future_done(futures):
  """Removes the currently done futures."""
  for i in xrange(len(futures) - 1, -1, -1):
    if futures[i].done():
      futures.pop(i)


def page_queries(queries, fetch_page_size=20, keys_only=True):
  """Yields all the items returned by the queries, page by page.
  It makes heavy use of fetch_page_async() for maximum efficiency.
  """
  queries = queries[:]
  futures = [q.fetch_page_async(fetch_page_size, keys_only=keys_only) for q in queries]
  while queries:
    i = futures.index(ndb.Future.wait_any(futures))
    results, cursor, more = futures[i].get_result()
    if not more:
      # Remove completed queries.
      queries.pop(i)
      futures.pop(i)
    else:
      futures[i] = queries[i].fetch_page_async(
        fetch_page_size, start_cursor=cursor, keys_only=keys_only)
    yield results


from google.appengine.ext import deferred
from google.appengine.runtime import DeadlineExceededError


class Mapper(object):
  # Subclasses should replace this with a model class (eg, model.Person).
  KIND = None

  # Subclasses can replace this with a list of (property, value) tuples to filter by.
  FILTERS = []

  def __init__(self):
    self.to_put = []
    self.to_delete = []
    self.tasks_queue = []

  def map(self, entity):
    """Updates a single entity.

    Implementers should return a tuple containing two iterables (to_update, to_delete).
    """
    return ([], [])

  def finish(self):
    """Called when the mapper has finished, to allow for any final work to be done."""
    pass

  def get_query(self):
    """Returns a query over the specified kind, with any appropriate filters applied."""
    q = self.KIND.query()
    for prop, value in self.FILTERS:
      q = q.filter(prop == value)
    q = q.order(self.KIND._key)
    return q

  def run(self, batch_size=100):
    """Starts the mapper running."""
    self._continue(None, batch_size)

  def _batch_write(self):
    """Writes updates and deletes entities in a batch."""
    if self.to_put:
      ndb.put_multi(self.to_put)
      self.to_put = []
    if self.to_delete:
      ndb.delete_multi(self.to_delete)
      self.to_delete = []

  def _continue(self, start_key, batch_size):
    q = self.get_query()
    # If we're resuming, pick up where we left off last time.
    if start_key:
      key_prop = getattr(self.KIND, '_key')
      q.filter(key_prop > start_key)
    # Keep updating records until we run out of time.
    try:
      # Steps over the results, returning each entity and its index.
      for i, entity in enumerate(q):
        map_updates, map_deletes = self.map(entity)
        self.to_put.extend(map_updates)
        self.to_delete.extend(map_deletes)
        # Do updates and deletes in batches.
        if (i + 1) % batch_size == 0:
          self._batch_write()
        # Record the last entity we processed.
        start_key = entity.key
      self._batch_write()
    except (Timeout,
            runtime.DeadlineExceededError,
            runtime.apiproxy_errors.CancelledError,
            runtime.apiproxy_errors.DeadlineExceededError,
            runtime.apiproxy_errors.OverQuotaError) as e:
      # Write any unfinished updates to the datastore.
      self._batch_write()
      # Queue a new task to pick up where we left off.
      tasks.addTask(self.tasks_queue, self._continue, start_key, batch_size)
      return
    self.finish()
