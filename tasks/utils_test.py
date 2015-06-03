import unittest
from utils import sending_rate


class UtilsTest(unittest.TestCase):
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


if __name__ == '__main__':
  unittest.main()