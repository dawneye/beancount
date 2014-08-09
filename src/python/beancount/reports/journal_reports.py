"""Report classes for all reports that display ending journals of accounts.
"""
import io
import re

from beancount.reports import report
from beancount.reports import tree_table
from beancount.reports import journal
from beancount.parser import printer
from beancount.parser import options
from beancount.core import data
from beancount.core import realization
from beancount.core import amount
from beancount.core import getters
from beancount.core import account_types
from beancount.core import complete
from beancount.core import inventory
from beancount.ops import prices
from beancount.utils import misc_utils


class JournalReport(report.HTMLReport,
                     metaclass=report.RealizationMeta):
    """Print out an account register/journal."""

    names = ['journal', 'register', 'account']

    @classmethod
    def add_args(cls, parser):
        parser.add_argument('-a', '--account',
                            action='store', default=None,
                            help="Account to render.")

    def render_real_htmldiv(self, real_root, options_map, file):
        if self.args.account:
            real_account = realization.get(real_root, self.args.account)
            if real_account is None:
                raise KeyError("Invalid account name: {}".format(self.args.account))
        else:
            real_account = real_root

        # Get the postings of the account.
        account_postings = realization.get_postings(real_account)

        # Render the page.
        journal.entries_table_with_balance(file, account_postings, self.formatter)


class ConversionsReport(report.HTMLReport):
    """Print out a report of all conversions."""

    names = ['conversions']

    @classmethod
    def add_args(cls, parser):
        parser.add_argument('-a', '--account',
                            action='store', default=None,
                            help="Account to render.")

    def render_htmldiv(self, entries, errors, options_map, file):
        # Return the subset of transaction entries which have a conversion.
        conversion_entries = [entry
                              for entry in misc_utils.filter_type(entries, data.Transaction)
                              if data.transaction_has_conversion(entry)]

        journal.entries_table(file, conversion_entries, self.formatter,
                              render_postings=True)

        # Note: Can we somehow add a balance at the bottom? Do we really need one?
        # conversion_balance = complete.compute_entries_balance(conversion_entries)


__reports__ = [
    JournalReport,
    ConversionsReport,
    ]
