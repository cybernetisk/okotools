#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import os.path
import csv
import io
import time
import pprint

from tripletex.tripletex import TripletexConnector, TripletexAccounts, TripletexProjects, TripletexLedger, TripletexDepartments

reports_path = '/var/okoreports/reports/'

SEMESTERS = (
    {'id': 1, 'text': 'vår', 'start': '-01-01', 'end': '-06-30'},
    {'id': 2, 'text': 'høst', 'start': '-07-01', 'end': '-12-31'},
)

# We cache previous accounting data, and it will only be refetched
# if we delete the aggregated-previous.txt file
DATE_RANGES = {
    'previous': ['2014-01-01', '2017-12-31'],
    'current': ['2018-01-01', '2019-12-31'],
}


def build_department_list(tripletex):
    departments = tripletex.get_department_list()
    ret = ''
    for department in departments:
        ret += '%s;%s;%s\n' % (
            department['id'],
            department['number'],
            department['name']
        )
    return ret


def build_account_list(tripletex):
    accounts = tripletex.get_accounts()
    ret = ''
    for account in accounts:
        ret += '%s;%s;%s;%s\n' % (
            account['id'],
            account['text'],
            account['group'],
            int(account['active'])
        )
    return ret


def get_aggregated_data(tripletex, ledger):
    def group_by_semester(row):
        sem = SEMESTERS[0 if row['Dato'].month < 7 else 1]
        return (
            '%d-%d' % (row['Dato'].year, sem['id']),
            {'year': row['Dato'].year, 'sem': sem}
        )

    def group_by_month(row):
        return (
            '%d-%d' % (row['Dato'].year, row['Dato'].month),
            {'year': row['Dato'].year, 'month': row['Dato'].month}
        )

    def group_by_avdeling(row):
        return (
            row['Avdelingsnummer'],
            row['Avdelingsnavn']
        )

    def group_by_project_number(row):
        return (
            row['Prosjektnummer'],
            row['Prosjektnavn']
        )

    def group_by_account_number(row):
        return (
            row['Kontonummer'],
            row['Kontonavn']
        )

    return tripletex.aggregate(ledger, group_by_month, group_by_avdeling, group_by_project_number, group_by_account_number)


def write_aggregated_data_report(data, output_handle, header=True):
    csv_out = csv.writer(output_handle, delimiter=';', quoting=csv.QUOTE_NONE)

    if header:
        csv_out.writerow([
            'Type',
            'Versjon',
            'År',
            'Måned',
            'Avdelingsnummer',
            #'Avdelingsnavn',
            'Prosjektnummer',
            #'Prosjektnavn',
            'Kontonummer',
            #'Kontonavn',
            'BeløpInn',
            'BeløpUt'
        ])

    for month in data.values():
        for avdeling_number, avdeling in month['data'].items():
            for project_number, project in avdeling['data'].items():
                for account_number, account in project['data'].items():
                    csv_out.writerow([
                        'Regnskap',
                        datetime.date.today().strftime('%Y%m%d'),
                        month['meta']['year'],
                        month['meta']['month'],
                        avdeling_number,
                        #avdeling['meta'],
                        project_number,
                        #project['meta'],
                        account_number,
                        #account['meta'],
                        account['data']['in'],
                        account['data']['out']
                    ])


def build_project_list(tripletex):
    ret = ''
    projects = tripletex.get_project_list()
    for project in projects:
        ret += '%s;%s;%s;%s\n' % (project['id'], project['parent'], project['number'], project['text'])
    return ret


def run(drop_cache=False):
    import settings

    ret = ''
    fetchLedger = True

    connector = TripletexConnector(credentials_provider=settings.credentials_provider)

    tt_departments = TripletexDepartments(settings.contextId, connector=connector)
    tt_accounts = TripletexAccounts(settings.contextId, connector=connector)
    tt_projects = TripletexProjects(settings.contextId, connector=connector)
    tt_ledger = TripletexLedger(settings.contextId, connector=connector)

    with open(reports_path + 'context_id.txt', 'w') as f:
        f.write(str(settings.contextId))

    # fetch ledger
    if fetchLedger:
        prev_file = reports_path + 'aggregated-previous.txt'

        # refetch previous data if missing
        if not os.path.isfile(prev_file) or drop_cache:
            ledger = tt_ledger.get_ledger(DATE_RANGES['previous'][0], DATE_RANGES['previous'][1])
            ret += 'Fetched ledger for %s to %s\n' % (DATE_RANGES['previous'][0], DATE_RANGES['previous'][1])

            prev_aggregated_data = get_aggregated_data(tt_ledger, ledger)
            with open(prev_file, 'w') as f:
                write_aggregated_data_report(prev_aggregated_data, f)

        else:
            ret += 'To fetch older ledger add ?drop_cache to url\n'

        # load previous data
        prev = ''
        with open(prev_file, 'r') as f:
            prev = f.read()

        # fetch current data
        ledger = tt_ledger.get_ledger(DATE_RANGES['current'][0], DATE_RANGES['current'][1])
        ret += 'Fetched ledger for %s to %s\n' % (DATE_RANGES['current'][0], DATE_RANGES['current'][1])

        aggregated_data = get_aggregated_data(tt_ledger, ledger)

        with open(reports_path + 'aggregated.txt', 'w') as f:
            # concatenate previous and current data
            f.write(prev)
            write_aggregated_data_report(aggregated_data, f, header=False)

    # fetch raw list of departments
    if True:
        with open(reports_path + 'departments.txt', 'w') as f:
            f.write(build_department_list(tt_departments))
        ret += 'Fetched department list\n'

    # fetch raw list of accounts
    if True:
        with open(reports_path + 'accounts.txt', 'w') as f:
            f.write(build_account_list(tt_accounts))
        ret += 'Fetched account list\n'

    # fetch raw list of projects
    if True:
        with open(reports_path + 'projects.txt', 'w') as f:
            f.write(build_project_list(tt_projects))
        ret += 'Fetched project list\n'

    ret += 'Reports saved to files in %s\n' % reports_path
    return ret

if __name__ == '__main__':
    print(run())
