import unittest

from demo_service.inventory import reserve_stock


class InventoryTests(unittest.TestCase):
    def test_normal_reservation(self):
        self.assertEqual(reserve_stock(10, 3), 7)

    def test_exact_stock(self):
        self.assertEqual(reserve_stock(5, 5), 0)

    def test_non_positive_quantity(self):
        for quantity in (0, -1):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                reserve_stock(10, quantity)

    def test_quantity_limit(self):
        with self.assertRaises(ValueError):
            reserve_stock(10, 6)

    def test_insufficient_stock(self):
        with self.assertRaises(ValueError):
            reserve_stock(2, 3)
