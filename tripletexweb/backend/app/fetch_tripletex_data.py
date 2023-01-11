import datetime
import os
import os.path
import csv

from tripletex.tripletex import Posting, PostingAggregate, TripletexConnectorV2, Tripletex

SEMESTERS = (
    {'id': 1, 'text': 'vår', 'start': '-01-01', 'end': '-06-30'},
    {'id': 2, 'text': 'høst', 'start': '-07-01', 'end': '-12-31'},
)

# We cache previous accounting data, and it will only be refetched
# if we delete the aggregated-previous.txt file
DATE_RANGES = {
    'previous': ['2014-01-01', '2022-01-01'],
    'current': ['2022-01-01', '2024-01-01'],
}


def build_department_list(tripletex: Tripletex) -> str:
    departments = tripletex.get_departments()
    ret = ''
    for department in departments:
        ret += '%s;%s;%s\n' % (
            department.id,
            department.number,
            department.name,
        )
    return ret


def build_account_list(tripletex: Tripletex) -> str:
    accounts = tripletex.get_accounts()
    ret = ''
    for account in accounts:
        ret += '%s;%s;%s;%s\n' % (
            account.id,
            account.text,
            account.group,
            int(account.active)
        )
    return ret


def get_aggregated_data(tripletex: Tripletex, postings: list[Posting]) -> PostingAggregate:
    def group_by_semester(row: Posting):
        sem = SEMESTERS[0 if row.date.month < 7 else 1]
        return (
            '%d-%d' % (row.date.year, sem['id']),
            {'year': row.date.year, 'sem': sem}
        )

    def group_by_month(row: Posting):
        return (
            '%d-%d' % (row.date.year, row.date.month),
            {'year': row.date.year, 'month': row.date.month}
        )

    def group_by_avdeling(row: Posting):
        return (
            str(row.department_number) if row.department_number is not None else "",
            row.department_name,
        )

    def group_by_project(row: Posting):
        return (
            str(row.project_id) if row.project_id is not None else "",
            {'id': row.project_id, 'name': row.project_name, 'number': row.project_number},
        )

    def group_by_account(row: Posting):
        return (
            str(row.account_number),
            row.account_name,
        )

    return tripletex.aggregate_postings(postings, group_by_month, group_by_avdeling, group_by_project, group_by_account)


def write_aggregated_data_report(data: PostingAggregate, output_handle, header=True):
    csv_out = csv.writer(output_handle, delimiter=';', quoting=csv.QUOTE_NONE)

    if header:
        csv_out.writerow([
            'Type',
            'Versjon',
            'År',
            'Måned',
            'Avdelingsnummer',
            #'Avdelingsnavn',
            'ProsjektId',
            #'Prosjektnavn',
            'Kontonummer',
            #'Kontonavn',
            'BeløpInn',
            'BeløpUt'
        ])

    for month in data.values():
        for avdeling_number, avdeling in month['data'].items():
            for project_id, project in avdeling['data'].items():
                for account_number, account in project['data'].items():
                    csv_out.writerow([
                        'Regnskap',
                        datetime.date.today().strftime('%Y%m%d'),
                        month['meta']['year'],
                        month['meta']['month'],
                        avdeling_number,
                        #avdeling['meta'],
                        project_id,
                        #project['meta']['name'],
                        account_number,
                        #account['meta'],
                        account['data']['in'],
                        account['data']['out']
                    ])


def build_project_list(tripletex: Tripletex) -> str:
    ret = ''
    projects = tripletex.get_projects()
    for project in projects:
        ret += '%s;%s;%s;%s\n' % (project.id, project.parent if project.parent is not None else "", project.number, project.text)
    return ret


def run(context_id: int, customer_token: str, employee_token: str, reports_path: str, drop_cache=False):
    ret = ''
    fetch_postings = True

    connector = TripletexConnectorV2(customer_token=customer_token, employee_token=employee_token)
    tripletex = Tripletex(context_id, connector=connector)

    with open(reports_path + 'context_id.txt', 'w') as f:
        f.write(str(context_id))

    # fetch postings
    if fetch_postings:
        prev_file = reports_path + 'aggregated-previous.txt'

        # refetch previous data if missing
        if not os.path.isfile(prev_file) or drop_cache:
            postings = tripletex.get_postings(date_start=DATE_RANGES['previous'][0], date_to=DATE_RANGES['previous'][1], account_start=3000)
            ret += 'Fetched postings for %s to %s (excl)\n' % (DATE_RANGES['previous'][0], DATE_RANGES['previous'][1])

            prev_aggregated_data = get_aggregated_data(tripletex, postings)
            with open(prev_file, 'w') as f:
                write_aggregated_data_report(prev_aggregated_data, f)

        else:
            ret += 'To fetch older ledger add ?drop_cache to url\n'

        # load previous data
        prev = ''
        with open(prev_file, 'r') as f:
            prev = f.read()

        # fetch current data
        postings = tripletex.get_postings(date_start=DATE_RANGES['current'][0], date_to=DATE_RANGES['current'][1], account_start=3000)
        ret += 'Fetched postings for %s to %s (excl)\n' % (DATE_RANGES['current'][0], DATE_RANGES['current'][1])

        aggregated_data = get_aggregated_data(tripletex, postings)

        with open(reports_path + 'aggregated.txt', 'w') as f:
            # concatenate previous and current data
            f.write(prev)
            write_aggregated_data_report(aggregated_data, f, header=False)

    # fetch raw list of departments
    if True:
        with open(reports_path + 'departments.txt', 'w') as f:
            f.write(build_department_list(tripletex))
        ret += 'Fetched department list\n'

    # fetch raw list of accounts
    if True:
        with open(reports_path + 'accounts.txt', 'w') as f:
            f.write(build_account_list(tripletex))
        ret += 'Fetched account list\n'

    # fetch raw list of projects
    if True:
        with open(reports_path + 'projects.txt', 'w') as f:
            f.write(build_project_list(tripletex))
        ret += 'Fetched project list\n'

    ret += 'Reports saved to files in %s\n' % reports_path
    return ret

if __name__ == '__main__':
    print(run())
