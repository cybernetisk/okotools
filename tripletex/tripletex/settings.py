# override this in settings_local.py

from typing import Callable
from tripletex.tripletex import Credentials

context_id: int = None  # type: ignore

# credentials_provider=lambda: Credentials(customer_token="aaa", employee_token="bbb")
credentials_provider: Callable[[], Credentials] = None  # type: ignore

# this is the link to a Google Spreadsheet feed - the document must be published for this to work
# e.g. https://spreadsheets.google.com/feeds/worksheets/1pAEq8O5NMkmEWvW-c6x_47abg5IO7HqPO5bs5J-iPt4/public/full?alt=json
# set to None to disable budget
budget_url = None

# the URL the user can go to and edit the spreadsheet
budget_edit_url = None

from settings_local import *
