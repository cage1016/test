# Copyright 2013 Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains an example of using Google Cloud Storage Signed URLs."""

import base64
import md5
import sys
import time
from datetime import datetime, timedelta
import os

import Crypto.Hash.SHA256 as SHA256
import Crypto.PublicKey.RSA as RSA
import Crypto.Signature.PKCS1_v1_5 as PKCS1_v1_5

import urllib
import settings


def SibPath(name):
  """Generate a path that is a sibling of this file.

  Args:
    name: Name of sibling file.
  Returns:
    Path to sibling file.
  """
  return os.path.join(os.path.dirname(__file__), name)

# The Google Cloud Storage API endpoint. You should not need to change this.
GCS_API_ENDPOINT = 'https://storage.googleapis.com'


class CloudStorageURLSigner(object):
  """Contains methods for generating signed URLs for Google Cloud Storage."""

  def __init__(self, key, client_id_email, gcs_api_endpoint, expires_after_seconds=60):
    """Creates a CloudStorageURLSigner that can be used to access signed URLs.

    Args:
      key: A PyCrypto private key.
      client_id_email: GCS service account email.
      gcs_api_endpoint: Base URL for GCS API.
      expiration: An instance of datetime.datetime containing the time when the
                  signed URL should expire.
      session: A requests.session.Session to use for issuing requests. If not
               supplied, a new session is created.
    """
    self.key = key
    self.client_id_email = client_id_email
    self.gcs_api_endpoint = gcs_api_endpoint

    expiration_dt = datetime.utcnow() + timedelta(seconds=expires_after_seconds)
    self.expiration = int(time.mktime(expiration_dt.timetuple()))

  def _Base64Sign(self, plaintext):
    """Signs and returns a base64-encoded SHA256 digest."""
    shahash = SHA256.new(plaintext)
    signer = PKCS1_v1_5.new(self.key)
    signature_bytes = signer.sign(shahash)
    return base64.b64encode(signature_bytes)

  def _MakeSignatureString(self, verb, path, content_md5, content_type):
    """Creates the signature string for signing according to GCS docs."""
    signature_string = ('{verb}\n'
                        '{content_md5}\n'
                        '{content_type}\n'
                        '{expiration}\n'
                        '{resource}')
    return signature_string.format(verb=verb,
                                   content_md5=content_md5,
                                   content_type=content_type,
                                   expiration=self.expiration,
                                   resource=path)

  def _MakeUrl(self, verb, path, content_type='', content_md5=''):
    """Forms and returns the full signed URL to access GCS."""
    base_url = '%s%s' % (self.gcs_api_endpoint, path)
    signature_string = self._MakeSignatureString(verb, path, content_md5,
                                                 content_type)
    signature_signed = self._Base64Sign(signature_string)
    query_params = {'GoogleAccessId': self.client_id_email,
                    'Expires': str(self.expiration),
                    'Signature': signature_signed}
    return base_url, query_params

  def Get(self, path):
    """Performs a GET request.

    Args:
      path: The relative API path to access, e.g. '/bucket/object'.

    Returns:
      An instance of requests.Response containing the HTTP response.
    """
    base_url, query_params = self._MakeUrl('GET', path)

    return '{base_url}?{querystring}'.format(base_url=base_url,
                                             querystring=urllib.urlencode(query_params))


def get_signed_url(gcs_filepath):
  key_text = open(SibPath('../privatekey.der')).read()
  private_key = RSA.importKey(key_text)

  signer = CloudStorageURLSigner(private_key,
                                 settings.SERVICE_ACCOUNT_EMAIL,
                                 GCS_API_ENDPOINT)

  return signer.Get(gcs_filepath)
