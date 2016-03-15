#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import csv
import io
import time
import pprint

from tripletex.tripletex import TripletexConnector, TripletexAccounts, TripletexProjects, TripletexLedger, TripletexDepartments

SEMESTERS = (
    {'id': 1, 'text': 'vår', 'start': '-01-01', 'end': '-06-30'},
    {'id': 2, 'text': 'høst', 'start': '-07-01', 'end': '-12-31'},
)


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


def write_aggregated_data_report(data, output_handle):
    csv_out = csv.writer(output_handle, delimiter=';', quoting=csv.QUOTE_NONE)

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


if __name__ == '__main__':
    # store contextId and credentials_provider in credentials.py
    # eg:
    #   contextId=1234
    #   credentials_provider=lambda: ('user@name', 'password')
    credentials_provider=None  # will ask for username and password by default
    path = '../tripletexweb/reports/'

    from export_settings import *

    fetchLedger = True

    connector = TripletexConnector(credentials_provider=credentials_provider)

    tt_departments = TripletexDepartments(contextId, connector=connector)
    tt_accounts = TripletexAccounts(contextId, connector=connector)
    tt_projects = TripletexProjects(contextId, connector=connector)
    tt_ledger = TripletexLedger(contextId, connector=connector)

    # fetch ledger
    if fetchLedger:
        ledger = tt_ledger.get_ledger('2014-01-01', '2016-12-31')
        print('Fetched ledger')

        aggregated_data = get_aggregated_data(tt_ledger, ledger)

        with open(path + 'aggregated.txt', 'w') as f:
            write_aggregated_data_report(aggregated_data, f)

    # fetch raw list of departments
    if True:
        with open(path + 'departments.txt', 'w') as f:
            f.write(build_department_list(tt_departments))
        print('Exported department list')

    # fetch raw list of accounts
    if True:
        with open(path + 'accounts.txt', 'w') as f:
            f.write(build_account_list(tt_accounts))
        print('Exported account list')

    # fetch raw list of projects
    if True:
        with open(path + 'projects.txt', 'w') as f:
            f.write(build_project_list(tt_projects))
        print('Exported project list')

    print('Reports saved to files in %s' % path)
