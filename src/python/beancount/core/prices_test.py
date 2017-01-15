__copyright__ = "Copyright (C) 2014-2016  Martin Blais"
__license__ = "GNU GPLv2"

import unittest
import datetime

from beancount.core.number import D
from beancount.core.amount import A
from beancount.core import inventory
from beancount.core import prices
from beancount.core import convert
from beancount.parser import cmptest
from beancount import loader


class TestPriceEntries(cmptest.TestCase):

    @loader.load_doc()
    def test_get_last_price_entries(self, entries, _, __):
        """
        2013-01-01 price  USD  1.01 CAD
        2013-02-01 price  USD  1.02 CAD
        2013-03-01 price  USD  1.03 CAD
        2013-04-01 price  USD  1.04 CAD
        2013-05-01 price  USD  1.05 CAD
        2013-06-01 price  USD  1.06 CAD
        2013-07-01 price  USD  1.07 CAD
        """
        self.assertEqualEntries("""
        2013-04-01 price  USD  1.04 CAD
        """, prices.get_last_price_entries(entries, datetime.date(2013, 5, 1)))

        self.assertEqualEntries("""
        2013-05-01 price  USD  1.05 CAD
        """, prices.get_last_price_entries(entries, datetime.date(2013, 5, 2)))

        self.assertEqualEntries("""
        2013-07-01 price  USD  1.07 CAD
        """, prices.get_last_price_entries(entries, datetime.date(2014, 1, 1)))

        self.assertEqualEntries("""
        """, prices.get_last_price_entries(entries, datetime.date(2012, 1, 1)))


class TestPriceMap(unittest.TestCase):

    def test_normalize_base_quote(self):
        self.assertEqual(('USD', 'CAD'),
                         prices.normalize_base_quote(('USD', 'CAD')))
        self.assertEqual(('USD', 'CAD'),
                         prices.normalize_base_quote(('USD/CAD')))
        with self.assertRaises(AssertionError):
            self.assertEqual(('USD', 'CAD'),
                             prices.normalize_base_quote(('HOOL/USD/CAD')))

    @loader.load_doc()
    def test_build_price_map(self, entries, _, __):
        """
        2013-06-01 price  USD  1.10 CAD

        ;; Try some prices at the same date.
        2013-06-02 price  USD  1.11 CAD
        2013-06-02 price  USD  1.12 CAD
        2013-06-02 price  USD  1.13 CAD

        ;; One after too.
        2013-06-03 price  USD  1.14 CAD

        ;; Try a few inverse prices.
        2013-06-05 price  CAD  0.86956 USD
        2013-06-06 price  CAD  0.86207 USD
        """
        price_map = prices.build_price_map(entries)

        self.assertEqual(2, len(price_map))
        self.assertEqual(set([('USD', 'CAD'), ('CAD', 'USD')]),
                         set(price_map.keys()))

        values = price_map[('USD', 'CAD')]
        expected = [(datetime.date(2013, 6, 1), D('1.10')),
                    (datetime.date(2013, 6, 2), D('1.13')),
                    (datetime.date(2013, 6, 3), D('1.14')),
                    (datetime.date(2013, 6, 5), D('1.15')),
                    (datetime.date(2013, 6, 6), D('1.16'))]
        for (exp_date, exp_value), (act_date, act_value) in zip(expected, values):
            self.assertEqual(exp_date, act_date)
            self.assertEqual(exp_value, act_value.quantize(D('0.01')))

        self.assertEqual(5, len(price_map[('CAD', 'USD')]))

    @loader.load_doc()
    def test_lookup_price_and_inverse(self, entries, _, __):
        """
        2013-06-01 price  USD  1.01 CAD
        """
        price_map = prices.build_price_map(entries)

        # Ensure that the forward exception includes the forward detail.
        try:
            prices._lookup_price_and_inverse(price_map, ('EUR', 'USD'))
            self.fail("Exception not raised")
        except KeyError as exc:
            self.assertRegex(str(exc), "('EUR', 'USD')")

    @loader.load_doc()
    def test_get_all_prices(self, entries, _, __):
        """
        2013-06-01 price  USD  1.01 CAD
        2013-06-03 price  USD  1.03 CAD
        2013-06-05 price  USD  1.05 CAD
        2013-06-07 price  USD  1.07 CAD
        2013-06-09 price  USD  1.09 CAD
        2013-06-11 price  USD  1.11 CAD
        """
        price_map = prices.build_price_map(entries)
        price_list = prices.get_all_prices(price_map, ('USD', 'CAD'))
        expected = [(datetime.date(2013, 6, 1), D('1.01')),
                    (datetime.date(2013, 6, 3), D('1.03')),
                    (datetime.date(2013, 6, 5), D('1.05')),
                    (datetime.date(2013, 6, 7), D('1.07')),
                    (datetime.date(2013, 6, 9), D('1.09')),
                    (datetime.date(2013, 6, 11), D('1.11'))]
        self.assertEqual(expected, price_list)

        inv_price_list = prices.get_all_prices(price_map, ('CAD', 'USD'))
        self.assertEqual(len(price_list), len(inv_price_list))

        # Test not found.
        with self.assertRaises(KeyError):
            prices.get_all_prices(price_map, ('EWJ', 'JPY'))

    @loader.load_doc()
    def test_get_latest_price(self, entries, _, __):
        """
        2013-06-01 price  USD  1.01 CAD
        2013-06-09 price  USD  1.09 CAD
        2013-06-11 price  USD  1.11 CAD
        """
        price_map = prices.build_price_map(entries)
        price_list = prices.get_latest_price(price_map, ('USD', 'CAD'))
        expected = (datetime.date(2013, 6, 11), D('1.11'))
        self.assertEqual(expected, price_list)

        # Test not found.
        result = prices.get_latest_price(price_map, ('EWJ', 'JPY'))
        self.assertEqual((None, None), result)

    @loader.load_doc()
    def test_get_price(self, entries, _, __):
        """
        2013-06-01 price  USD  1.00 CAD
        2013-06-10 price  USD  1.50 CAD
        2013-07-01 price  USD  2.00 CAD
        """
        price_map = prices.build_price_map(entries)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 5, 15))
        self.assertEqual(None, price)
        self.assertEqual(None, date)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 6, 1))
        self.assertEqual(D('1.00'), price)
        self.assertEqual(datetime.date(2013, 6, 1), date)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 6, 5))
        self.assertEqual(D('1.00'), price)
        self.assertEqual(datetime.date(2013, 6, 1), date)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 6, 10))
        self.assertEqual(D('1.50'), price)
        self.assertEqual(datetime.date(2013, 6, 10), date)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 6, 20))
        self.assertEqual(D('1.50'), price)
        self.assertEqual(datetime.date(2013, 6, 10), date)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 7, 1))
        self.assertEqual(D('2.00'), price)
        self.assertEqual(datetime.date(2013, 7, 1), date)

        date, price = prices.get_price(price_map, 'USD/CAD', datetime.date(2013, 7, 15))
        self.assertEqual(D('2.00'), price)
        self.assertEqual(datetime.date(2013, 7, 1), date)

        # With no date, should devolved to get_latest_price().
        date, price = prices.get_price(price_map, 'USD/CAD', None)
        self.assertEqual(D('2.00'), price)
        self.assertEqual(datetime.date(2013, 7, 1), date)

        # Test not found.
        result = prices.get_price(price_map, ('EWJ', 'JPY'))
        self.assertEqual((None, None), result)

    @loader.load_doc()
    def test_ordering_same_date(self, entries, _, __):
        """
        ;; The last one to appear in the file should be selected.
        2013-06-02 price  USD  1.13 CAD
        2013-06-02 price  USD  1.12 CAD
        2013-06-02 price  USD  1.11 CAD
        """
        price_map = prices.build_price_map(entries)

        self.assertEqual(2, len(price_map))
        self.assertEqual(set([('USD', 'CAD'), ('CAD', 'USD')]),
                         set(price_map.keys()))

        values = price_map[('USD', 'CAD')]
        expected = [(datetime.date(2013, 6, 2), D('1.11'))]
        for (exp_date, exp_value), (act_date, act_value) in zip(expected, values):
            self.assertEqual(exp_date, act_date)
            self.assertEqual(exp_value, act_value.quantize(D('0.01')))

        self.assertEqual(1, len(price_map[('CAD', 'USD')]))
