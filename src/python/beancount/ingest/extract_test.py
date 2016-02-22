__author__ = "Martin Blais <blais@furius.ca>"

from os import path
import re
import unittest
import datetime
import io
import os
import textwrap
from unittest import mock

from beancount.utils import test_utils
from beancount.utils import misc_utils
from beancount.core import data
from beancount.parser import parser
from beancount.parser import printer
from beancount import loader
from beancount.ingest import extract
from beancount.ingest import importer
from beancount.ingest import scripts_utils


class TestScriptExtractFromFile(test_utils.TestCase):

    def test_extract_from_file__empty(self):
        imp = mock.MagicMock()
        imp.identify = mock.MagicMock(return_value=True)
        imp.extract = mock.MagicMock(return_value=[])
        new_entries, dup_entries = extract.extract_from_file('blabla.ofx', imp)
        self.assertEqual([], new_entries)
        self.assertEqual([], dup_entries)

    def test_extract_from_file__ensure_sorted(self):
        entries, _, __ = loader.load_string("""

          2016-02-03 * "C"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-01 * "A"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-02 * "B"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

        """)

        imp = mock.MagicMock()
        imp.identify = mock.MagicMock(return_value=True)
        imp.extract = mock.MagicMock(return_value=entries)
        new_entries, dup_entries = extract.extract_from_file('blabla.ofx', imp)
        self.assertEqual(3, len(entries))
        self.assertTrue(misc_utils.is_sorted(new_entries, key=lambda entry: entry.date))
        self.assertEqual([], dup_entries)

    def test_extract_from_file__ensure_sanity(self):
        entries, _, __ = loader.load_string("""
          2016-02-01 * "A"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD
        """)
        # Break something.
        entries[-1] = entries[-1]._replace(narration=42)

        imp = mock.MagicMock()
        imp.identify = mock.MagicMock(return_value=True)
        imp.extract = mock.MagicMock(return_value=entries)
        with self.assertRaises(AssertionError):
            extract.extract_from_file('blabla.ofx', imp)

    def test_extract_from_file__min_date(self):
        entries, _, __ = loader.load_string("""

          2016-02-01 * "A"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-02 * "B"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-03 * "C"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

        """)
        imp = mock.MagicMock()
        imp.identify = mock.MagicMock(return_value=True)
        imp.extract = mock.MagicMock(return_value=entries)
        new_entries, dup_entries = extract.extract_from_file(
            'blabla.ofx', imp, min_date=datetime.date(2016, 2, 2))
        self.assertEqual(2, len(new_entries))
        self.assertEqual([datetime.date(2016, 2, 2), datetime.date(2016, 2, 3)],
                         [entry.date for entry in new_entries])
        self.assertEqual([], dup_entries)

    def test_extract_from_file__existing_entries(self):
        entries, _, __ = loader.load_string("""

          2016-02-01 * "A"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-02 * "B"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-03 * "C"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

          2016-02-04 * "D"
            Assets:Account1    10.00 USD
            Assets:Account2   -10.00 USD

        """)
        imp = mock.MagicMock()
        imp.identify = mock.MagicMock(return_value=True)
        imp.extract = mock.MagicMock(return_value=[entries[1], entries[3]])

        new_entries, dup_entries = extract.extract_from_file('blabla.ofx', imp, entries)
        self.assertEqual(2, len(dup_entries))
        self.assertEqual([datetime.date(2016, 2, 2), datetime.date(2016, 2, 4)],
                         [entry.date for entry in new_entries])

        # Check that the entries have also been marked.
        marked_entries = [entry
                          for entry in new_entries
                          if extract.DUPLICATE_META in entry.meta]
        self.assertEqual(dup_entries, marked_entries)


class TestPrintExtractedEntries(scripts_utils.TestScriptsBase, unittest.TestCase):

    class ExtractTestImporter(importer.ImporterProtocol):
        def __init__(self):
            super().__init__()
            pass
        def file_account(self, _):
            return 'Assets:Account1'

    @mock.patch.object(extract, 'extract_from_file')
    def test_print_extracted_entries(self, mock_extract_from_file):
        entries, _, __ = parser.parse_string("""

          2016-02-01 * "A"
            Assets:Account1    11.11 USD
            Assets:Account2   -11.11 USD

          2016-02-01 * "B"
            Assets:Account1    22.22 USD
            Assets:Account3   -22.22 USD

        """)
        mock_extract_from_file.return_value = entries

        entries[-2].meta[extract.DUPLICATE_META] = True

        importer = TestPrintExtractedEntries.ExtractTestImporter()
        oss = io.StringIO()
        extract.print_extracted_entries(importer, entries, oss)

        self.assertEqual(textwrap.dedent("""\

        ;; beancount.ingest.extract_test.ExtractTestImporter

        ; 2016-02-01 * "A"
        ;   Assets:Account1   11.11 USD
        ;   Assets:Account2  -11.11 USD

        2016-02-01 * "B"
          Assets:Account1   22.22 USD
          Assets:Account3  -22.22 USD

        """).strip(), oss.getvalue().strip())



class _LoaderImporter(importer.ImporterProtocol):
    """A mock importer which loads the file contents as a Beancount file itself.
    This is an odd trick for testing: I just put the expected extracted entries
    in the file and read them.
    """
    def __init__(self, filename, account):
        super().__init__()
        self.filename = filename
        self.account = account

    def identify(self, file):
        return path.basename(file.name) == path.basename(self.filename)

    def extract(self, file):
        entries, _, __ = loader.load_file(file.name)
        return entries

    def file_account(self, _):
        return self.account


class TestScriptExtract(test_utils.TestTempdirMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.config_filename = path.join(self.tempdir, 'extract.import')
        with open(self.config_filename, 'w') as file:
            file.write(textwrap.dedent("""\
              #!/usr/bin/env python3
              from beancount.ingest import extract_test
              CONFIG = [
                extract_test._LoaderImporter('checking.dl', 'Assets:Checking'),
                extract_test._LoaderImporter('credit.dl', 'Liabilities:CreditCard'),
              ]
            """))

        self.downloads = path.join(self.tempdir, 'Downloads')
        os.mkdir(self.downloads)

        self.dl_checking = path.join(self.downloads, 'checking.dl')
        with open(self.dl_checking, 'w') as file:
            file.write(textwrap.dedent("""\

              plugin "beancount.plugins.auto_accounts"

              2016-06-08 * "Withdrawal"
                Assets:Checking           -300.00 USD
                Assets:Cash

              2016-06-10 * "Electricity"
                Assets:Checking            -48.34 USD
                Expenses:Electricity

              2016-06-14 * "Internet"
                Assets:Checking            -48.34 USD
                Expenses:Internet

            """))

        self.dl_credit = path.join(self.downloads, 'credit.dl')
        with open(self.dl_credit, 'w') as file:
            file.write(textwrap.dedent("""\

              plugin "beancount.plugins.auto_accounts"

              2016-06-04 * "Drinks"
                Liabilities:CreditCard     -32.23 USD
                Expenses:Alcohol

              2016-06-07 * "Books"
                Liabilities:CreditCard     -87.30 USD
                Expenses:Books

              2016-06-10 * "Clothing"
                Liabilities:CreditCard     -87.30 USD
                Expenses:Clothing

            """))

    def test_extract(self):
        with test_utils.capture('stdout', 'stderr') as (stdout, stderr):
            test_utils.run_with_args(extract.main,
                                     [self.config_filename,
                                      path.join(self.tempdir, 'Downloads')])
        output = stdout.getvalue()

        self.assertRegex(output, r'/checking.dl')
        self.assertRegex(output, r'_LoaderImporter')
        self.assertRegex(output, r'Assets:Cash +300.00 USD')
        self.assertRegex(output, r'Expenses:Electricity +48.34 USD')
        self.assertRegex(output, r'Expenses:Internet +48.34 USD')

        self.assertRegex(output, r'/credit.dl')
        self.assertRegex(output, r'_LoaderImporter')
        self.assertRegex(output, r'Expenses:Alcohol +32.23 USD')
        self.assertRegex(output, r'Expenses:Books +87.30 USD')
        self.assertRegex(output, r'Expenses:Clothing +87.30 USD')

    def test_extract_with_previous_entries(self):
        existing_filename = path.join(self.tempdir, 'existing.beancount')
        with open(existing_filename, 'w') as file:
            file.write(textwrap.dedent("""\

              plugin "beancount.plugins.auto_accounts"

              2016-06-02 * "Rent"
                Assets:Checking          -1000.00 USD
                Expenses:Rent

              2016-06-08 * "Withdrawal"
                Assets:Checking           -300.00 USD
                Assets:Cash


              2016-06-01 * "Dinner"
                Liabilities:CreditCard     -47.34 USD
                Expenses:Restaurant

              2016-06-03 * "Groceries"
                Liabilities:CreditCard     -82.32 USD
                Expenses:Groceries

              2016-06-04 * "Drinks"
                Liabilities:CreditCard     -32.23 USD
                Expenses:Alcohol

            """))

        with test_utils.capture('stdout', 'stderr') as (stdout, stderr):
            test_utils.run_with_args(extract.main,
                                     ['--existing={}'.format(existing_filename),
                                      self.config_filename,
                                      path.join(self.tempdir, 'Downloads')])
        output = stdout.getvalue()

        self.assertRegex(output, r'/checking.dl')
        self.assertRegex(output, r'_LoaderImporter')
        self.assertRegex(output, r'; +Assets:Cash +300.00 USD')
        self.assertRegex(output, r'Expenses:Electricity +48.34 USD')
        self.assertRegex(output, r'Expenses:Internet +48.34 USD')

        self.assertRegex(output, r'/credit.dl')
        self.assertRegex(output, r'_LoaderImporter')
        self.assertRegex(output, r'; +Expenses:Alcohol +32.23 USD')
        self.assertRegex(output, r'Expenses:Books +87.30 USD')
        self.assertRegex(output, r'Expenses:Clothing +87.30 USD')
