#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time

from tripletex import *


def get_accounts_list(tripletex):
    accounts = tripletex.get_accounts()
    ret = ''
    for account in accounts:
        ret += '%s\t%s\t%s\t%s\n' % (
            account['id'],
            account['text'],
            account['group'],
            int(account['active'])
        )
    return ret


def get_accounts_report(tripletex, year, sem):
    project_number = 40041

    project_id = tripletex.get_project_id(project_number)
    result = tripletex.get_report_result(date_start=str(year) + sem['start'], date_end=str(year) + sem['end'],
                                         project_id=project_id)

    ret = ''
    for account in result:
        ret += '%s\t\t%s\t\t\t%s\t%s\tregnskap\t%s\t%s\n' % (project_number, account[0], year, sem['text'],
                                                             time.strftime('%Y%m%d'), str(account[1]).replace('.', ','))
    return ret


def get_projects_report(tripletex, year, sem):
    result = tripletex.get_report_projects(date_start=str(year) + sem['start'], date_end=str(year) + sem['end'])

    ret = ''
    for project in result:
        ret += '%s\t\t\t%s\t%s\tregnskap\t%s\t%s\t%s\n' % (project[0], year, sem['text'], time.strftime('%Y%m%d'),
                                                           str(project[2]).replace('.', ','),
                                                           str(project[3]).replace('.', ','))
    return ret


def get_projects_list(tripletex):
    ret = ''
    projects = tripletex.get_project_list()
    for project in projects:
        ret += '%s\t%s\t%s\n' % (project['parent'], project['number'], project['text'])
    return ret


if __name__ == '__main__':
    tt = Tripletex()

    home = os.path.expanduser('~')
    path = home + '/Dropbox/Økonomigruppa/8 Budsjett og regnskap (internt)/2016/'

    with open(path + 'accounts_list.txt', 'w') as f:
        f.write(get_accounts_list(tt))
    print('Exported accounts list')

    with open(path + 'projects_list.txt', 'w') as f:
        f.write(get_projects_list(tt))
    print('Exported projects list')

    with open(path + 'accounts_report.txt', 'w') as f:
        f.write(get_accounts_report(tt, 2014, SEMESTERS[0]))
        f.write(get_accounts_report(tt, 2014, SEMESTERS[1]))
        f.write(get_accounts_report(tt, 2015, SEMESTERS[0]))
        f.write(get_accounts_report(tt, 2015, SEMESTERS[1]))
    print('Exported accounts report')

    with open(path + 'projects_report.txt', 'w') as f:
        f.write(get_projects_report(tt, 2014, SEMESTERS[0]))
        f.write(get_projects_report(tt, 2014, SEMESTERS[1]))
        f.write(get_projects_report(tt, 2015, SEMESTERS[0]))
        f.write(get_projects_report(tt, 2015, SEMESTERS[1]))
    print('Exported projects report')

    print('Reports saved to files in %s' % path)
