import io
import os

from dotenv import load_dotenv

from app import fetch_budget_data

load_dotenv()

budget_credentials_file = os.environ.get("OKOREPORTS_BUDGET_CREDENTIALS_FILE", None)
budget_spreadsheet_id = os.environ.get("OKOREPORTS_BUDGET_SPREADSHEET_ID", None)

class TestBudget:
    def test_budget(self):
        out = io.StringIO()

        edit_url = fetch_budget_data.export_budget(
            spreadsheet_id=budget_spreadsheet_id,
            credentials_file=budget_credentials_file,
            output_handle=out,
        )

        print(out.getvalue())
        print(edit_url)

    def test_get_name_from_range(self):
        assert fetch_budget_data.get_name_from_range("'Something'!A1:C3") == "Something"
        assert fetch_budget_data.get_name_from_range("Something!A1:C3") == "Something"
        assert fetch_budget_data.get_name_from_range("Something") == "Something"
