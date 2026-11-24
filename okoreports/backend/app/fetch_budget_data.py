import csv
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def get_float(val):
    if type(val) == float or type(val) == int:
        return val

    try:
        return float(val.replace(' ', '').replace(',', '.').replace(' ', ''))
    except ValueError:
        return 0

def get_name_from_range(range: str) -> str:
    return re.compile(r"^'?(.+?)'?!.+").sub("\\1", range)

def export_budget(spreadsheet_id, credentials_file, output_handle) -> str:
    """Retrieve spreadsheet data and write CSV to output_handle.

    Returns edit URL for spreadsheet.
    """
    credentials = Credentials.from_service_account_file(credentials_file)
    service = build("sheets", "v4", credentials=credentials)

    spreadsheet_info = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    ranges = [
        "'{}'!A1:I1000".format(sheet["properties"]["title"])
        for sheet in spreadsheet_info["sheets"]
    ]

    result = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=ranges,
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute()

    csv_out = csv.writer(output_handle, delimiter=';', quoting=csv.QUOTE_NONE)
    csv_out.writerow([
        'Type',
        'Versjon',
        'År',
        'Måned',
        'Avdelingsnummer',
        'Prosjektnummer',
        'Kontonummer',
        'BeløpInn',
        'BeløpUt',
        'Beskrivelse'
    ])

    COL_AAR = 0
    COL_SEMESTER = 1
    COL_AVDELING = 2
    COL_PROSJEKT = 3
    COL_KONTO = 4
    COL_INNTEKTER = 5
    COL_KOSTNADER = 6
    COL_KOMMENTAR = 7
    COL_TYPE = 8

    def col(row, idx):
        if len(row) < idx + 1:
            return ''
        return row[idx]

    for value_range in result["valueRanges"]:
        version = get_name_from_range(value_range['range'])

        for row in value_range["values"][1:]:
            # ignore rows without year
            try:
                aar = int(col(row, COL_AAR))
            except ValueError:
                continue

            # ignore rows not including anything useful
            if col(row, COL_INNTEKTER) == '' and col(row, COL_KOSTNADER) == '':
                continue

            csv_out.writerow([
                col(row, COL_TYPE) or 'Budsjett',
                version,
                aar,
                6 if col(row, COL_SEMESTER) == 'vår' else (12 if col(row, COL_SEMESTER) == 'høst' else 0),
                col(row, COL_AVDELING),
                col(row, COL_PROSJEKT),
                col(row, COL_KONTO),
                get_float(col(row, COL_INNTEKTER)) * -1,
                get_float(col(row, COL_KOSTNADER)),
                col(row, COL_KOMMENTAR)
            ])

    return spreadsheet_info["spreadsheetUrl"]

def run(spreadsheet_id: str, credentials_file: str, reports_path: str):
    if spreadsheet_id is None or credentials_file is None:
        return 'Fetching data from budget is not configured - skipping budget'

    with open(reports_path + 'budget.txt', 'w') as f:
        budget_edit_url = export_budget(spreadsheet_id, credentials_file, f)

    with open(reports_path + 'budget_url.txt', 'w') as f:
        f.write(budget_edit_url)

    return 'Fetched data from budget and updated report'

if __name__ == '__main__':
    print(run())
