import unittest

from utils import sending_rate, replace_edm_csv_property
from utils import sending_rate, timeit

import time


class UtilsSendingRateTest(unittest.TestCase):
  def test_sending_rate_sum(self):
    rate1, sum1 = sending_rate(1, 1, 1, 1000)
    rate2, sum2 = sending_rate(1, 1, 24, 1000)
    rate3, sum3 = sending_rate(2, 1, 24, 1000)

    self.assertEqual(2000, sum1)
    self.assertEqual(2000, sum2)
    self.assertEqual(6000, sum3)

    self.assertEqual([2000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     rate1)

    self.assertEqual([91, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83, 83],
                     rate2)


class UtilsEdmReplaceTest(unittest.TestCase):
  def setUp(self):
    self.content = '<html><body><p>{{id}}</p><div>{{name}}</div>{{e}}<body></html>'
    self.user_data = {u'name': u'User29817', u'FirstName': u'Test', u'Quota': u'0', u'global_index': 18681,
                      u'FirstLogin': u'0', u'LastLogin': u'0', u'number_of_hour': 15, u'inner_index': 1180,
                      u'email': u'user29817@test2.sparapps.us', u'id': 22222, u'cmem_num': 383747383}
    self.targets = 'id,name'

  def test_replace_edm_csv_property(self):
    html_content = replace_edm_csv_property(self.content, self.user_data, self.targets)

    print html_content

    self.assertEqual(html_content, '<html><body><p>22222</p><div>User29817</div><body></html>')


class TimeItTest(unittest.TestCase):
  def test_timeit(self):
    class A(object):
      @timeit
      def run(self):
        time.sleep(5)

    a = A()
    a.run()

    te = time.time()

    self.assertEqual((te - a.ts).__int__(), 5)
    self.assertEqual(self.executed_time, 5)


if __name__ == '__main__':
  unittest.main()