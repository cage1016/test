from google.appengine import runtime
from datastore_utils import incremental_map


class AsyncMapper(object):
  # Subclasses should replace this with a model class (eg, model.Person).
  KIND = None

  # Subclasses can replace this with a list of (property, value) tuples to filter by.
  FILTERS = []

  # Maximum time to spend processing before enqueueing the next task in seconds.
  MAX_EXECUTION_TIME = 500

  def __init__(self):
    pass

  def map_fn(self, items):
    """map_fn:
      callback that accepts a list of objects to map and optionally
      returns a list of ndb.Future.
    """
    raise NotImplementedError()

  def finish(self, more):
    """Called when the mapper has finished, to allow for any final work to be done."""
    pass

  def get_query(self):
    """Returns a query over the specified kind, with any appropriate filters applied."""
    q = self.KIND.query()
    for prop, value in self.FILTERS:
      q = q.filter(prop == value)
    # q = q.order(self.KIND._key)
    return q

  def run(self):
    """Starts the mapper running."""
    self._continue()

  def enqueue(self, c):
    """re enqueue processing.

    Returns:
      tasks.addTask
    """
    raise NotImplementedError()

  def _continue(self, start_cursor=None):
    more, curosr = incremental_map([self.get_query()],
                                   map_fn=self.map_fn,
                                   start_cursor=start_cursor,
                                   max_execute_time=self.MAX_EXECUTION_TIME)

    self.finish(more)

    if more:
      self.enqueue(curosr)
