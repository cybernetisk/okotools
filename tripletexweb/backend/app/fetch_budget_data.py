import csv

import requests

def getFloat(val):
    try:
        return float(val.replace(' ', '').replace(',', '.').replace(' ', ''))
    except ValueError:
        return 0

def export_budget(budget_url, output_handle):
    csv_out = csv.writer(output_handle, delimiter=';', quoting=csv.QUOTE_NONE)
    r = requests.get(budget_url).json()

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

    for sheet in r['feed']['entry']:
        version = sheet['title']['$t']

        link = [x for x in sheet['link'] if x['type'] == 'text/csv'][0]['href']

        csv_data = requests.get(link).content.decode('utf-8').split('\n')
        csv_f = csv.reader(csv_data)

        is_first = True
        for row in csv_f:
            if is_first:
                is_first = False
                continue

            # ignore rows not including anything useful
            if row[COL_AVDELING] == '' and row[COL_PROSJEKT] == '' and row[COL_INNTEKTER] == '' and row[COL_KOSTNADER] == '':
                continue

            csv_out.writerow([
                row[COL_TYPE] if len(row) >= 9 and row[COL_TYPE] != "" else 'Budsjett',
                version,
                row[COL_AAR],
                6 if row[COL_SEMESTER] == 'vår' else (12 if row[COL_SEMESTER] == 'høst' else 0),
                row[COL_AVDELING],
                row[COL_PROSJEKT],
                row[COL_KONTO],
                getFloat(row[COL_INNTEKTER]) * -1,
                getFloat(row[COL_KOSTNADER]),
                row[COL_KOMMENTAR]
            ])

def run(budget_url: str, budget_edit_url: str, reports_path: str):
    if budget_url is None:
        return 'Fetching data from budget is disabled - skipping budget'

    with open(reports_path + 'budget.txt', 'w') as f:
        export_budget(budget_url, f)

    with open(reports_path + 'budget_url.txt', 'w') as f:
        if budget_edit_url != None:
            f.write(budget_edit_url)

    return 'Fetched data from budget and updated report'

if __name__ == '__main__':
    print(run())
