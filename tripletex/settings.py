# override this in settings_local.py
contextId = None

# credentials_provider=lambda: ('user@name', 'password')
credentials_provider = None

# this is the link to a Google Spreadsheet feed
# e.g. https://spreadsheets.google.com/feeds/worksheets/1pAEq8O5NMkmEWvW-c6x_47abg5IO7HqPO5bs5J-iPt4/public/full?alt=json
# set to None to disable budget
budget_url = None

# where reports should be saved
reports_path = '../tripletexweb/web/reports/'

from settings_local import *
