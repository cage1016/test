# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Utility to convert a Data Export API reponse into TSV.

This provides utitlites to both print TSV files to the standard output
as well as directly to a file. This logic handles all the utf-8 conversion.

  GetTsvFilePrinter: Returns an instantiated object to output to files.
  GetTsvScreenPrinter: Returns an instantiated object to output to the screen.
  UnicodeWriter(): Utf-8 encodes output.
  ExportPrinter(): Converts the Data Export API response into tabular data.
"""

__author__ = 'api.nickm@ (Nick Mihailovski)'

import codecs
import csv
import StringIO
import sys
import types


# A list of special characters that need to be escaped.
SPECIAL_CHARS = ('+', '-', '/', '*', '=')
# TODO(nm): Test leading numbers.


def GetJSONStringPrinter(f):
    """Returns a ExportPrinter object to output to std.stdout."""
    writer = UnicodeWriter(f, dialect='excel-tab', delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    return ExportPrinter(writer)


# Wrapper to output to utf-8. Taken mostly / directly from Python docs:
# http://docs.python.org/library/csv.html
class UnicodeWriter(object):
    """A CSV writer which uses the csv module to output csv compatible formats.

    Will write rows to CSV file "f", which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = StringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    # pylint: disable=g-bad-name
    def writerow(self, row):
        """Writes a CSV row.

        Args:
          row: list The row to write to the CSV output.
        """

        self.writer.writerow(row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    # pylint: disable=g-bad-name
    def writerows(self, rows):
        """Writes rows for CSV output.

        Args:
          rows: list of rows to write.
        """
        for row in rows:
            self.writerow(row)


class ExportPrinter(object):
    """Utility class to output a the data feed as tabular data."""

    def __init__(self, writer):
        """Initializes the class.

        Args:
          writer: Typically an instance of UnicodeWriter. The interface for this
              object provides two methods, writerow and writerow, which
              accepts a list or a list of lists respectively and process them as
              needed.
        """
        self.writer = writer

    def Output(self, results):
        """Outputs formatted rows of data retrieved from the Data Export API.

        This uses the writer object to output the data in the Data Export API.

        Args:
          results: The response from the data export API.
        """

        if not len(results):
            self.writer.writerow('No Results found')

        else:
            self.writer.writerow([key for key, value in results[0].iteritems()])

            for row in results:
                row_values = []

                for key, value in row.iteritems():
                    if isinstance(value, unicode):
                        row_values.append(unicode.encode(value, 'utf8'))
                    else:
                        row_values.append(value)

                self.writer.writerow(row_values)


def ExcelEscape(input_value):
    """Escapes the first character of a string if it is special in Excel.

    Args:
      input_value: string The value to escape.

    Returns:
      A string that has the first character escaped if it is special.
    """
    if input_value and input_value[0] in SPECIAL_CHARS:
        return "'" + input_value

    return input_value

