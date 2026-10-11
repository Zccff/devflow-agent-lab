import unittest

from demo_service.billing import calculate_total


class RoundingTests(unittest.TestCase):
    def test_2675_rounds_half_up(self):
        self.assertEqual(calculate_total("2.675", 1), "2.68")

    def test_2685_rounds_half_up(self):
        self.assertEqual(calculate_total("2.685", 1), "2.69")

    def test_batch_price_rounds_after_multiplication(self):
        self.assertEqual(calculate_total("2.675", 3), "8.03")
