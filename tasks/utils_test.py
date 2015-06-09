# coding: utf-8

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
    self.content = u'<a href="http://www.treemall.com.tw/EDMLog/EDM.jsp?pid=<?pid?>&amp;url=http://www.treemall.com.tw/edm/120726morning/auto/m150608.shtml?utm_source=treemall%26utm_medium=edm%26utm_campaign=<?ep_id?>%26campaign=<?ep_id?>" id="selfLink" name="selfLink" class="t12gg">※ 若是您無法正常瀏覽，請點選這裡，直接到TreeMall泰贈點網站上讀取</a><img src="http://www.treemall.com.tw/EDMLog/readA.jsp?id=<?pid?>" width="0" />'
    self.user_data = {"gi": 90, "ii": 90, "hr": 0, "email": "xxx@kimo.com", "cmem_num": "1263175"}
    self.targets = '<?pid?>:cmem_num,<?sd_id?>:pid'

  def test_replace_edm_csv_property(self):
    html_content = replace_edm_csv_property(self.content, self.user_data, self.targets)
    self.assertEqual(html_content,
                     u'<a href="http://www.treemall.com.tw/EDMLog/EDM.jsp?pid=1263175&amp;url=http://www.treemall.com.tw/edm/120726morning/auto/m150608.shtml?utm_source=treemall%26utm_medium=edm%26utm_campaign=<?ep_id?>%26campaign=<?ep_id?>" id="selfLink" name="selfLink" class="t12gg">※ 若是您無法正常瀏覽，請點選這裡，直接到TreeMall泰贈點網站上讀取</a><img src="http://www.treemall.com.tw/EDMLog/readA.jsp?id=1263175" width="0" />')


  def test_replace_edm_csv_empty(self):
    html_content = replace_edm_csv_property(self.content, self.user_data, '')
    self.assertEqual(html_content,
                     u'<a href="http://www.treemall.com.tw/EDMLog/EDM.jsp?pid=<?pid?>&amp;url=http://www.treemall.com.tw/edm/120726morning/auto/m150608.shtml?utm_source=treemall%26utm_medium=edm%26utm_campaign=<?ep_id?>%26campaign=<?ep_id?>" id="selfLink" name="selfLink" class="t12gg">※ 若是您無法正常瀏覽，請點選這裡，直接到TreeMall泰贈點網站上讀取</a><img src="http://www.treemall.com.tw/EDMLog/readA.jsp?id=<?pid?>" width="0" />')


class TimeItTest(unittest.TestCase):
  def test_timeit(self):
    class A(object):
      @timeit
      def run(self):
        time.sleep(2)

    a = A()
    a.run()

    te = time.time()

    self.assertEqual((te - a.ts).__int__(), 2)


if __name__ == '__main__':
  unittest.main()