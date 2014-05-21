"""Getter functions that operate on lists of entries to return various lists of
things that they reference, accounts, tags, links, currencies, etc.
"""
from collections import defaultdict

from beancount.core.data import Transaction, Open, Close
from beancount.core import account
from beancount.utils import misc_utils


# FIXME: Ideally this would live under ops, pending dependencies.


class GetAccounts:
    """Accounts gatherer.
    """
    def __call__(self, entries):
        """Gather the list of accounts from the list of entries.

        Args:
          entries: A list of directive instances.
        Returns:
          A list of Account instances.
        """
        # FIXME: Convert this to a set().
        accounts = {}
        for entry in entries:
            method = getattr(self, entry.__class__.__name__)
            for account in method(entry):
                accounts[account] = account
        return accounts

    def Transaction(_, entry):
        """Process a Transaction directive.

        Args:
          entry: An instance of Transaction.
        Yields:
          The accounts of the legs of the transaction.
        """
        for posting in entry.postings:
            yield posting.account

    def Pad(_, entry):
        """Process a Pad directive.

        Args:
          entry: An instance of Pad.
        Returns:
          The two accounts of the Pad directive.
        """
        return (entry.account, entry.account_pad)

    def _one(_, entry):
        """Process directives with a single account attribute.

        Args:
          entry: An instance of a directive.
        Returns:
          The single account of this directive.
        """
        return (entry.account,)

    def _zero(_, entry):
        """Process directives with no accounts.

        Args:
          entry: An instance of a directive.
        Returns:
          An empty list
        """
        return ()

    # Associate all the possible directives with their respective handlers.
    Open = Close = Balance = Note = Document = _one
    Event = Price = _zero


def get_accounts(entries):
    """Gather all the accounts references by a list of directives.

    Args:
      entries: A list of directive instances.
    Returns:
      A list of Account instances.
    """
    return GetAccounts()(entries)


def get_account_components(entries):
    """Gather all the account components available in the given directives.

    Args:
      entries: A list of directive instances.
    Returns:
      A set of strings, the unique account components, including the root
      account names.
    """
    accounts = get_accounts(entries)
    components = set()
    for account_name in accounts:
        components.update(account_name.split(account.sep))
    return components


def get_all_tags(entries):
    """Return a list of all the tags seen in the given entries.

    Args:
      entries: A list of directive instances.
    Returns:
      A set of tag strings.
    """
    all_tags = set()
    for entry in misc_utils.filter_type(entries, Transaction):
        if entry.tags:
            all_tags.update(entry.tags)
    return all_tags


def get_all_payees(entries):
    """Return a list of all the unique payees seen in the given entries.

    Args:
      entries: A list of directive instances.
    Returns:
      A set of payee strings.
    """
    all_payees = set()
    for entry in misc_utils.filter_type(entries, Transaction):
        all_payees.add(entry.payee)
    all_payees.discard(None)
    return all_payees


def get_leveln_parent_accounts(account_names, n, nrepeats=0):
    """Return a list of all the unique leaf names are level N in an account hierarchy.

    Args:
      account_names: A list of account names (strings)
      n: The level to cross-cut. 0 is for root accounts.
      nrepeats: A minimum number of times a leaf is required to be present in the
        the list of unique account names in order to be returned by this function.
    Returns:
      A list of leaf node names.
    """
    leveldict = defaultdict(int)
    for account_name in set(account_names):
        components = account_name.split(account.sep)
        if n < len(components):
            leveldict[components[n]] += 1
    levels = {level
              for level, count in leveldict.items()
              if count > nrepeats}
    return sorted(levels)


def get_min_max_dates(entries):
    """Return the minimum and amximum dates in the list of entries.

    Args:
      entries: A list of directive instances.
    Returns:
      A pair of datetime.date dates, the minimum and maximum dates seen in the
      directives.
    """
    if not entries:
        return (None, None)
    return (entries[0].date, entries[-1].date)


def get_active_years(entries):
    """Yield all the years that have at least one entry in them.

    Args:
      entries: A list of directive instances.
    Yields:
      Unique dates see in the list of directives.
    """
    seen = set()
    prev_year = None
    for entry in entries:
        year = entry.date.year
        if year != prev_year:
            prev_year = year
            assert year not in seen
            seen.add(year)
            yield year


def get_account_open_close(entries):
    """Fetch the open/close entries for each of the accounts.

    Args:
      entries: A list of directive instances.
    Returns:
      A map of Account instance to pairs of (open-directive,
      close-directive) tuples.
    """
    open_closes_map = defaultdict(lambda: [None, None])
    for entry in misc_utils.filter_type(entries, (Open, Close)):
        index = 0 if isinstance(entry, Open) else 1
        open_closes_map[entry.account][index] = entry
    return open_closes_map
