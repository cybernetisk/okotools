#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import requests
import sys

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

            csv_out.writerow([
                row[8] if len(row) >= 9 and row[8] != "" else 'Budsjett',
                version,
                row[0],
                6 if row[1] == 'vår' else (12 if row[1] == 'høst' else 0),
                row[2],
                row[3],
                row[4],
                getFloat(row[5]) * -1,
                getFloat(row[6]),
                row[7]
            ])

if __name__ == '__main__':
    import settings
    if settings.budget_url is None:
        print('Fetching data from budget is disabled - skipping budget')
        sys.exit(0)

    with open(settings.reports_path + 'budget.txt', 'w') as f:
        export_budget(settings.budget_url, f)

    with open(settings.reports_path + 'budget_url.txt', 'w') as f:
        if settings.budget_edit_url != None:
            f.write(settings.budget_edit_url)

    print('Fetched data from budget and updated report')
