import re
import logging

from apiclient.errors import HttpError


DEFAULT_CHUNK_SIZE = 512 * 1024


class GCSIterator(object):
  """
  Reference:
  Parsing Large CSV Blobs on Google App Engine by Daniel Thompson @ d4nt
  http://d4nt.com/parsing-large-csv-blobs-on-google-app-engine

  Implement Google Cloud Storage csv.DictReader Iterator
  """

  def __init__(self, request, progress=0, chunksize=DEFAULT_CHUNK_SIZE):
    self._request = request
    self._uri = request.uri
    self._chunksize = chunksize
    self._progress = progress
    self._total_size = None
    self._done = False

    self._last_line = ""
    self._line_num = 0
    self._lines = []
    self._buffer = None
    self._done = False

    self._bytes_read = 0

  def __iter__(self):
    return self

  def next(self):
    if not self._buffer or len(self._lines) == (self._line_num + 1):
      if self._lines:
        self._last_line = self._lines[self._line_num]

      if not self._done:
        self._buffer, self._done = self.read()

      else:
        self._buffer = ''

      self._lines = re.split('\r|\n|\r\n', self._buffer)
      self._line_num = 0

      # Handle special case where our block just happens to end on a new line
      if self._buffer[-1:] == "\n" or self._buffer[-1:] == "\r":
        self._lines.append("")

    if not self._buffer:
      raise StopIteration

    if self._line_num == 0 and len(self._last_line) > 0:
      # print 'fixing'
      result = self._last_line + self._lines[self._line_num] + "\n"

    else:
      result = self._lines[self._line_num] + "\n"

    # check csv header
    if self._bytes_read == 0:
      if not re.match('email', result.lower().replace('"','')):
        raise ValueError('csv header must contain "email or EMAIL" property.')

      else:
        result = result.lower()

    self._bytes_read += len(result)
    self._line_num += 1

    return result


  def read(self, num_retries=0):
    headers = {
      'range': 'bytes=%d-%d' % (
        self._progress, self._progress + self._chunksize)
    }
    logging.info('read bytes=%d-%d/%s' % (self._progress,
                                          (self._progress + self._chunksize),
                                          str(self._total_size) if self._total_size else '*'))
    http = self._request.http

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

