"""
Unit tests for summarization.
"""

import unittest
import sys
from datetime import date
import textwrap
import functools

from beancount.core.account import Account, is_income_statement_account
from beancount.core.realization import realize, dump_tree_balances, compare_realizations, real_cost_as_dict
from beancount.core.pad import pad
from beancount.core.summarize import summarize, transfer, open_at_date

from beancount import parser
from beancount.parser import parsedoc


DO_PRINT = object()

def summarizedoc(date, other_account):

    def summarizedoc_deco(fun):
        """Decorator that parses, pads and summarizes, and realizes the function's
        docstring as an argument."""
        @functools.wraps(fun)
        def newfun(self):
            entries, parse_errors, options = parser.parse_string(textwrap.dedent(fun.__doc__))
            assert not parse_errors, parse_errors
            entries, pad_errors = pad(entries)
            assert not pad_errors, pad_errors

            real_accounts = realize(entries, do_check=True)

            sum_entries, _ = summarize(entries, date, other_account)
            sum_real_accounts = realize(sum_entries, do_check=True)

            # print('---')
            # for entry in before: print(entry)
            # print('---')
            # for entry in after: print(entry)
            # print('---')

            result = None
            try:
                result = fun(self, entries, sum_entries, real_accounts, sum_real_accounts)
            except AssertionError:
                result = DO_PRINT
                raise
            finally:
                if result is DO_PRINT:
                    print("REAL")
                    dump_tree_balances(real_accounts, sys.stdout)
                    print("SUM_REAL")
                    dump_tree_balances(sum_real_accounts, sys.stdout)

        return newfun
    return summarizedoc_deco


OPENING_BALANCES = Account('Equity:Opening-Balancess', 'Equity')
TRANSFER_BALANCES = Account('Equity:Retained-Earnings', 'Equity')

class TestSummarization(unittest.TestCase):

    @summarizedoc(date(2012, 1, 1), OPENING_BALANCES)
    def test_sum_basic(self, entries, sum_entries, real_accounts, sum_real_accounts):
        """
          2011-01-01 open Assets:Checking

          2011-01-01 open Income:Job

          2011-02-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD

          2012-02-01 * "Salary Next year"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD
        """
        self.assertTrue(compare_realizations(real_accounts, sum_real_accounts))
        self.assertTrue(sum_real_accounts[OPENING_BALANCES.name].postings)

    @summarizedoc(date(2012, 1, 1), OPENING_BALANCES)
    def test_with_conversions(self, entries, sum_entries, real_accounts, sum_real_accounts):
        """
          2011-01-01 open Assets:Checking

          2011-01-01 open Income:Job

          2011-02-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD

          2011-02-15 * "Conversion"
            Assets:Checking       -1000 USD
            Assets:Checking        1000 CAD @ 1 USD
        """
        self.assertTrue(compare_realizations(real_accounts, sum_real_accounts))
        self.assertTrue(sum_real_accounts[OPENING_BALANCES.name].postings)


    @summarizedoc(date(2012, 1, 1), OPENING_BALANCES)
    def test_limit_date(self, entries, sum_entries, real_accounts, sum_real_accounts):
        """
          2011-01-01 open Assets:Checking
          2011-01-01 open Income:Job

          2011-06-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD

          2012-01-01 check Assets:Checking  1000 USD
        """
        self.assertTrue(compare_realizations(real_accounts, sum_real_accounts))
        self.assertTrue(sum_real_accounts[OPENING_BALANCES.name].postings)

    @parsedoc
    def test_transfer_and_summarization(self, entries, errors, options):
        """
          2011-01-01 open Assets:Checking
          2011-01-01 open Income:Job
          2011-01-01 open Expenses:Restaurant

          2011-06-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD

          2011-06-02 * "Eating out"
            Expenses:Restaurant      80 USD
            Assets:Checking

          2012-01-01 check Assets:Checking  920 USD

          2012-06-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD
        """

        entries, pad_errors = pad(entries)

        report_date = date(2012, 1, 1)
        tran_entries = transfer(entries, report_date,
                                is_income_statement_account, TRANSFER_BALANCES)

        sum_entries, _ = summarize(tran_entries, report_date, OPENING_BALANCES)
        real_accounts = realize(sum_entries, do_check=True)

        self.assertEqual(real_cost_as_dict(real_accounts),
                         {'Assets:Checking': 'Inventory(1920.00 USD)',
                          'Equity:Opening-Balancess': 'Inventory()',
                          'Equity:Retained-Earnings': 'Inventory(-920.00 USD)',
                          'Expenses:Restaurant': 'Inventory()',
                          'Income:Job': 'Inventory(-1000.00 USD)'})


class TestTransferBalances(unittest.TestCase):

    @parsedoc
    def test_basic_transfer(self, entries, errors, options):
        """
          2011-01-01 open Assets:Checking
          2011-01-01 open Income:Job

          2011-02-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD

          2012-02-01 * "Salary Next year"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD
        """
        real_accounts = realize(entries, do_check=True)
        self.assertEqual(real_cost_as_dict(real_accounts),
                         {'Assets:Checking': 'Inventory(2000.00 USD)',
                          'Income:Job': 'Inventory(-2000.00 USD)'})

        tran_entries = transfer(entries, date(2012, 6, 1),
                                is_income_statement_account, TRANSFER_BALANCES)

        real_accounts = realize(tran_entries, do_check=True)
        self.assertEqual(real_cost_as_dict(real_accounts),
                         {'Assets:Checking': 'Inventory(2000.00 USD)',
                          'Income:Job': 'Inventory()',
                          'Equity:Retained-Earnings': 'Inventory(-2000.00 USD)'})


class TestOpenAtDate(unittest.TestCase):

    @parsedoc
    def test_open_at_date(self, entries, errors, options):
        """
          2011-02-01 open Assets:CheckingA
          2011-02-28 open Assets:CheckingB
          2011-02-10 open Assets:CheckingC
          2011-02-20 open Assets:CheckingD
          2011-01-20 open Income:Job

          2011-06-01 * "Salary"
            Income:Job            -1000 USD
            Assets:Checking        1000 USD

        """
        open_entries = open_at_date(entries, date(2012, 1, 1))
        dates = [entry.date for entry in open_entries]
        self.assertEqual(dates, sorted(dates))



# FIXME: Add a test of two open directives for the same account, should fail.


