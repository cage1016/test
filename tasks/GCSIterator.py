import random
import re
import logging
import time

from apiclient.errors import HttpError

DEFAULT_CHUNK_SIZE = 512 * 1024


class GCSIterator(object):
  """
  Reference:
  Parsing Large CSV Blobs on Google App Engine by Daniel Thompson @ d4nt
  http://d4nt.com/parsing-large-csv-blobs-on-google-app-engine

  Implement Google Cloud Storage csv.DictReader Iterator
  """

  def __init__(self, request, capacity, progress=0, chunksize=DEFAULT_CHUNK_SIZE):
    self._request = request
    self._uri = request.uri
    self._chunksize = chunksize
    self._progress = progress
    self._init_progress = progress
    self._total_size = None
    self._done = False

    self._last_line = ""
    self._line_num = 0
    self._lines = []
    self._buffer = None
    self._done = False
    self._done_and_last_line = False

    self._bytes_read = 0
    self._capacity = capacity

    # Stubs for testing.
    self._sleep = time.sleep
    self._rand = random.random

  def __iter__(self):
    return self

  def next(self):
    if (not self._buffer or len(self._lines) == (self._line_num + 1)) and not self._done_and_last_line:
      if self._lines:
        self._last_line = self._lines[self._line_num]

      if not self._done:
        self._buffer, self._done = self.read(3)

      else:
        self._buffer = ''

      self._lines = re.split('\r|\n|\r\n', self._buffer)
      self._line_num = 0

      # Handle special case where our block just happens to end on a new line
      if self._buffer[-1:] == "\n" or self._buffer[-1:] == "\r":
        self._lines.append("")

    if not self._buffer:
      if self._done and not self._last_line:
        raise StopIteration

      else:
        self._done_and_last_line = True

    if self._line_num == 0 and len(self._last_line) > 0:
      # print 'fixing'
      result = self._last_line + self._lines[self._line_num] + "\n"

    else:
      result = self._lines[self._line_num] + "\n"

    # check csv header
    if self._bytes_read == 0 and self._init_progress == 0:
      if not re.match('email', result.lower().replace('"', '')):
        raise ValueError('csv header must contain "email or EMAIL" property.')

      else:
        result = result.lower()

    self._bytes_read += len(result)
    if not self._done_and_last_line:
      self._line_num += 1

    else:
      self._last_line = ''

    return result


  def read(self, num_retries=0):
    """Get the next chunk of the download.

    Args:
      num_retries: Integer, number of times to retry 500's with randomized
            exponential backoff. If all retries fail, the raised HttpError
            represents the last request. If zero (default), we attempt the
            request only once.

    Returns:
      (status, done): (MediaDownloadStatus, boolean)
         The value of 'done' will be True when the media has been fully
         downloaded.

    Raises:
      apiclient.errors.HttpError if the response was not a 2xx.
      httplib2.HttpLib2Error if a transport error has occured.
    """

    try:

      headers = {
        'range': 'bytes=%d-%d' % (
          self._progress, self._progress + self._chunksize)
      }
      http = self._request.http
      # logging.info('read bytes=%d-%d/%s' % (self._progress,
      #                                       (self._progress + self._chunksize),
      #                                       str(self._total_size) if self._total_size else '*'))

      for retry_num in xrange(num_retries + 1):
        if retry_num > 0:
          self._sleep(self._rand() * 2 ** retry_num)
          logging.warning(
            'Retry #%d for media download: GET %s, following status: %d'
            % (retry_num, self._uri, resp.status))

        resp, content = http.request(self._uri, headers=headers)
        if resp.status < 500:
          break

      if resp.status in [200, 206]:
        if 'content-location' in resp and resp['content-location'] != self._uri:
          self._uri = resp['content-location']
        self._progress += len(content)

        if 'content-range' in resp:
          content_range = resp['content-range']
          length = content_range.rsplit('/', 1)[1]
          self._total_size = int(length)

        if self._progress == self._total_size:
          self._done = True
        return content, self._done
      else:
        raise HttpError(resp, content, uri=self._uri)

    except Exception as e:
      logging.warning('gcs iterator error manual retry')
      logging.error(e.message)

      self._sleep(self._rand() * 2 ** 2)
      self.read()
