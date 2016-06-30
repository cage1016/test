# coding: utf-8

import sys
import site
import os
import csv
import httplib2


PYTHON_VERSION = 'python%d.%d' % (sys.version_info[0], sys.version_info[1])


def add(path, index=1):
  """Insert site dir or virtualenv at a given index in sys.path.

  Args:
    path: relative path to a site dir or virtualenv.
    index: sys.path position to insert the site dir.

  Raises:
    ValueError: path doesn't exist.
  """
  venv_path = os.path.join(path, 'lib', PYTHON_VERSION, 'site-packages')
  if os.path.isdir(venv_path):
    site_dir = venv_path
  elif os.path.isdir(path):
    site_dir = path
  else:
    raise ValueError('virtualenv: cannot access %s: '
                     'No such virtualenv or site directory' % path)

  sys_path = sys.path[:]
  del sys.path[index:]
  site.addsitedir(site_dir)
  sys.path.extend(sys_path[index:])


add('lib')

from apiclient.discovery import build as discovery_build

import unittest
from GCSIterator import GCSIterator

DEVELOPER_KEY = 'AIzaSyCe1PxvzGZYMkqlCOaClwM2V5MJfmvh7zg'

from oauth2client.client import SignedJwtAssertionCredentials

client_email = '24182559640-m9p986sd0khfe2b6hc0m018f9b3bob6f@developer.gserviceaccount.com'
with open("cheerspoint-mail-186705c1c0b3.pem") as f:
  private_key = f.read()


def get_authenticated_service():
  print 'Authenticating...'
  credentials = SignedJwtAssertionCredentials(client_email,
                                              private_key,
                                              'https://www.googleapis.com/auth/devstorage.full_control')

  print 'Constructing Google Cloud Storage service...'
  http = credentials.authorize(httplib2.Http())
  return discovery_build('storage', 'v1', http=http)


class GCSIteratorTest(unittest.TestCase):
  def setUp(self):
    gcs_service = get_authenticated_service()
    bucket_name = u'cage-20160705-edm.appspot.com'
    txt_object_name = u'ipwarmup/cage@mitac.com.tw/kaichu1016_0000110.csv'

    request = gcs_service.objects().get_media(bucket=bucket_name, object=txt_object_name.encode('utf8'))
    self.test_iterator = GCSIterator(request, 2 * 1024)


  def test_iterator(self):
    reader = csv.DictReader(self.test_iterator, skipinitialspace=True, delimiter=',')
    for row in reader:
      print row
      if row:
        self.assertEqual({'email': 'kaichu1016+0000000@gmail.com', 'name': 'cage0000000'}, row)
        break


if __name__ == '__main__':
  unittest.main()