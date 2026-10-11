import unittest

from demo_service.billing import calculate_total
from demo_service.service import checkout


class CheckoutTests(unittest.TestCase):
    def test_checkout_returns_total_and_currency(self):
        result = checkout("demo-user:2000", "9.95", 2, 1000)
        self.assertEqual(result["total"], "19.90")
        self.assertEqual(result["currency"], "CNY")

    def test_checkout_rejects_expired_credential(self):
        self.assertEqual(checkout("demo-user:900", "9.95", 2, 1000)["status"], 401)

    def test_non_positive_quantity_is_rejected(self):
        for quantity in (0, -1):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                calculate_total("9.95", quantity)

    def test_normal_price_has_two_decimal_places(self):
        self.assertEqual(calculate_total("3.5", 2), "7.00")
