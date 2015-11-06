#!/usr/bin/env python3

# pip3 install requests cookielib

import csv
import requests
import http.cookiejar
import urllib.parse
import re
from bs4 import BeautifulSoup
from collections import OrderedDict

# settings are stored in settings.py, example:
# username = "username"
# password = "password"
from settings import *

SEMESTERS = (
    {'id': 1, 'text': 'vår', 'start': '-01-01', 'end': '-06-30'},
    {'id': 2, 'text': 'høst', 'start': '-07-01', 'end': '-12-31'},
)


class TripletexBase:
    session = None

    def __init__(self, cookies_file="cookies.txt"):
        self.cookies_file = cookies_file

    def get_session_object(self):
        if self.session is not None:
            return self.session

        cj = http.cookiejar.MozillaCookieJar(self.cookies_file)
        try:
            cj.load()
        except FileNotFoundError:
            pass

        self.session = requests.Session()
        self.session.cookies = cj

        return self.session

    def request_get(self, *args, **kwargs):
        s = self.get_session_object()
        r = s.get(*args, **kwargs)

        if r.status_code == 401:
            self.do_login()
            r = s.get(*args, **kwargs)
            if r.status_code == 401:
                raise NotLoggedInException(r.text)

        s.cookies.save(ignore_discard=True)
        return r

    def request_post(self, *args, **kwargs):
        s = self.get_session_object()
        r = s.post(*args, **kwargs)

        if r.status_code == 401:
            self.do_login()
            r = s.post(*args, **kwargs)
            if r.status_code == 401:
                raise NotLoggedInException(r.text)

        s.cookies.save()
        return r

    @staticmethod
    def get_login_data():
        return 'username=%s&password=%s&act=login&contentUrl=&site=no&recaptcha=false' % (
            urllib.parse.quote(username), urllib.parse.quote(password))

    def do_login(self):
        r = self.get_session_object().post('https://tripletex.no/execute/login',
                                           data=self.get_login_data(),
                                           headers={'content-type': 'application/x-www-form-urlencoded'},
                                           allow_redirects=False)

        if r.status_code != 302:
            raise LoginFailedException(r.text)


class Tripletex(TripletexBase):
    @staticmethod
    def get_url_ledger(year):
        """year = 2015"""
        url = 'https://tripletex.no/execute/viewJournal?javaClass=no.tripletex.tcp.web.JournalForm&' + \
              'documentationComponent=145&contextId=2845076&isExpandedFilter=true&period.startDate=%d-01-01&' + \
              'period.endOfPeriodDate=%d-12-31&period.periodType=1&=%d&registeredById=-1&updatedById=-1&' + \
              'numberSeriesId=89077&startNumber=&endNumber=&accountId=-1&minAmountString=&maxAmountString=&' + \
              'amountType=2&ascending=false&rowCount=2&act=content&scope=ajaxContent'
        return url % (year, year, year)

    def get_ledger(self, year):
        return self.request_get(self.get_url_ledger(year))

    def get_next_ledger_number(self, year):
        data = self.get_ledger(2015)
        if data.status_code == 401:
            self.do_login()
            data = self.get_ledger(2015)

        m = re.search(r'Bilag nummer (\d+)-(\d+)', data.text)
        if m is None:
            raise LedgerNumberFailed(data.text)

        return int(m.group(1)) + 1

    def get_accounts(self):
        url = "https://tripletex.no/execute/chartOfAccounts?act=content&scope=ui-id-2&contextId=2845076"
        r = self.request_get(url)

        if r.status_code != 200:
            raise TripletexException("Could not get list of accounts")

        soup = BeautifulSoup(r.text, 'html.parser')
        account_list = []

        for tr in soup.tbody.find_all('tr'):
            if len(tr.contents) < 8:
                continue

            account_list.append({
                'id': tr.contents[1].text.strip(),
                'text': tr.contents[2].text.strip(),
                'group': tr.contents[3].text.strip(),
                'active': len(tr.contents[7].text.strip()) == 0
            })

        return account_list

    def get_project_list_old(self):
        url = "https://tripletex.no/JSON-RPC?syncSystem=0&contextId=2845076"

        post_data = {
            "marshallSpec": [
                "id",
                "number",
                "displayName",
                "hierarchyNameAndNumber",
                "projectManagerNameAndNumber",
                "departmentId",
                "projectCategoryId",
                "customerName"
            ],
            "className": "JSONRpcClient.RequestExtraInfo",
            "id": '81',
            "method": "Project.searchForProjects",
            "params": [
                '2845076',
                '-1',
                '-1',
                '-1',
                '-1',
                '-1',
                '0',
                '1',
                '-1',
                'false',
                'false',
                {
                    "javaClass": "java.util.Date",
                    "time": '1443650400000'
                },
                {
                    "javaClass": "java.util.Date",
                    "time": '1446332400000'
                },
                ''
            ]
        }

        r = self.request_post(url, json=post_data)
        if r.status_code != 200:
            raise TripletexException("Unexpected return code from JSON-RPC when fetching project list")

        if 'error' in r.json():
            raise TripletexException("Upload failed: %s" % r.json()['error'])

        project_list = []

        data = r.json()
        for project in data['result']:
            project_list.append({
                'id': project['id'],
                'number': project['number'],
                'text': project['displayName']
            })

        return project_list

    def get_project_list(self):
        q = OrderedDict()
        q['javaClass'] = 'no.tripletex.tcp.web.ListProjectsExtForm'
        q['documentationComponent'] = '162'
        q['contextId'] = '2845076'
        q['viewMode'] = '0'
        q['isExpandedFilter'] = 'true'
        q['isOrder'] = '1'
        q['filter'] = '-1'
        q['selectedProjectManagerId'] = '-1'
        q['selectedProjectDepartmentId'] = '-1'
        q['projectCategoryId'] = '-1'
        q['customerId'] = '-1'
        q['customerCategoryId1'] = '-1'
        q['sortType'] = '-1'
        q['ascending'] = 'true'
        q['registeredDateStart'] = ''
        q['registeredDateEnd'] = ''
        q['closedDateStart'] = ''
        q['closedDateEnd'] = ''
        q['viewTotal'] = 'false'
        q['viewInvoicedIncomeOnly'] = 'false'
        q['act'] = 'content'
        q['scope'] = 'ajaxContent'

        query_string = urllib.parse.urlencode(q)
        url = "https://tripletex.no/execute/listProjectsExt?" + query_string

        r = self.request_get(url)
        if r.status_code != 200:
            raise TripletexException("Could not fetch project list")

        project_list = []
        for tr in re.findall(r'<tr.*?>(.+?)</tr>', r.text):
            tdlist = re.findall(r'<td.*?>(.+?)</td>', tr)

            if len(tdlist) == 7:
                project_id = re.search(r'projectId=(\d+)&', tdlist[1]).group(1)

                start_and_end = re.sub(r'<[^>]*?>', '', tdlist[5])
                m = re.match(r'^\s*(.+?)( (.+?))?\s*$', start_and_end)

                project_list.append({
                    'id': project_id,
                    'text': re.sub(r'  +', ' ', re.sub(r'<[^>]*?>', '', tdlist[2]).strip()),
                    'start': m.group(1),
                    'end': m.group(3)
                })

        return self.__project_list_find_parent(project_list)

    @staticmethod
    def __project_list_find_parent(project_list):
        levels = {-1: ''}
        next_id = 1
        new_project_list = []

        for project in project_list:
            level = int(len(re.sub(r'^((\. )*).*', r'\1', project['text'])) / 4)

            parent = levels[level - 1]

            m = re.match(r'^(\. )*((\d+) )?(.*)', project['text'])
            if not m:
                raise Exception('could not parse project line: %s' % project['text'])

            text = m.group(4)

            if m.group(3):
                number = int(m.group(3))
            else:
                number = next_id
                next_id += 1

            new_project = dict(project)
            new_project['number'] = number
            new_project['text'] = text
            new_project['parent'] = parent
            new_project['level'] = level
            new_project_list.append(new_project)

            levels[level] = number

        return new_project_list

    def get_report_result(self, date_start, date_end, project_id=None, include_sub_projects=False):
        q = OrderedDict()
        q['javaClass'] = "no.tripletex.tcp.web.ResultReport2Form"
        q['documentationComponent'] = "133"
        q['contextId'] = "2845076"
        q['viewMode'] = "0"
        q['isExpandedFilter'] = "true"
        q['period.startDate'] = date_start  # "2014-01-01"
        q['period.endOfPeriodDate'] = date_end  # "2015-12-31"
        q['period.periodType'] = "1"
        q['selectedCustomerId'] = "-1"
        q['selectedVendorId'] = "-1"
        q['selectedDepartmentId'] = "-1"
        q['selectedEmployeeId'] = "-1"
        q['selectedProjectId'] = str(project_id) if project_id else "-1"
        q['includeSubProjectsOfSelectedProject'] = "true" if include_sub_projects else "false"
        q['selectedProductId'] = "-1"
        q['budgetType'] = "0"
        q['viewAccounts'] = "true"
        q['viewLastYear'] = "false"
        q['viewAccountingPeriods'] = "false"
        q['viewSoFar'] = "false"
        q['viewUnusedReportGroups'] = "false"
        q['showDecimalVerdi'] = "false"
        q['csv'] = "true"
        q['csvHeader'] = "true"
        q['csvEncoding'] = "UTF-8"
        q['csvSeparator'] = ";"
        q['csvQualifier'] = '"'
        q['csvDecimal'] = "."
        q['csvLineBreak'] = "\n"

        query_string = urllib.parse.urlencode(q)
        url = "https://tripletex.no/execute/resultReport2?" + query_string

        r = self.request_get(url)
        if r.status_code != 200:
            print(r.text)
            raise TripletexException("Could not fetch report, error code: %s" % r.status_code)

        result_list = []

        csvobj = csv.reader(r.text.strip().split('\n'), delimiter=';')
        is_first = True
        for row in csvobj:
            if is_first:
                is_first = False
                continue
            result_list.append([int(row[0]), float(row[-6])])

        return result_list

    def get_report_projects(self, date_start, date_end, project_id=None, include_sub_projects=True):
        q = OrderedDict()
        q['javaClass'] = 'no.tripletex.tcp.web.ProjectResultReportForm'
        q['documentationComponent'] = '259'
        q['contextId'] = '2845076'
        q['isExpandedFilter'] = 'true'
        q['period.startDate'] = date_start  # "2014-01-01"
        q['period.endOfPeriodDate'] = date_end  # "2015-12-31"
        q['period.periodType'] = '4'
        q['selectedCustomerId'] = '-1'
        q['selectedProjectManagerId'] = '-1'
        q['selectedProjectId'] = str(project_id) if project_id else "-1"
        q['isOffer'] = '0'
        q['isInternal'] = '-1'
        q['selectedProjectCategoryId'] = '-1'
        q['selectedProjectDepartmentId'] = '-1'
        q['viewSubProjects'] = "true" if include_sub_projects else "false"
        q['viewProjectsNoMovements'] = 'false'
        q['viewSoFar'] = 'false'
        q['viewAccountingPeriods'] = 'false'
        q['viewIncome'] = 'true'
        q['viewCosts'] = 'true'
        q['viewResult'] = 'false'
        q['viewCoverage'] = 'false'
        q['csv'] = 'true'
        q['csvHeader'] = 'true'
        q['csvEncoding'] = 'UTF-8'
        q['csvSeparator'] = ';'
        q['csvQualifier'] = '"'
        q['csvDecimal'] = '.'
        q['csvLineBreak'] = '\n'

        query_string = urllib.parse.urlencode(q)
        url = "https://tripletex.no/execute/projectResultReport?" + query_string

        r = self.request_get(url)
        if r.status_code != 200:
            print(r.text)
            raise TripletexException("Could not fetch report of projects, error code: %s" % r.status_code)

        result_list = []

        csvobj = csv.reader(r.text.strip().split('\n'), delimiter=';')
        is_first = True
        for row in csvobj:
            if is_first:
                is_first = False
                continue

            project = re.match(r'(\d+) (.+)', row[0])
            result_list.append([
                project.group(1),
                project.group(2),
                float(row[1]),
                float(row[2])
            ])

        return result_list

    def import_gbat10(self, data):
        if not isinstance(data, str):
            raise ValueError("Need a unicode string as GBAT10-data")

        files = [('file', ('bilag.csv', data.encode('utf-8'), 'text/plain')), ]
        r = self.request_post('https://tripletex.no/execute/uploadCentral?contextId=2845076', files=files)
        # [{"id":"29027318","revision":"1","name":"bilag.csv","size":"0","readableSize":"0","uid":"0","checksum":"da39a3ee5e6b4b0d3255bfef95601890afd80709"}]

        if r.status_code != 200:
            raise UploadFailedException(r.text)

        file_data = r.json()[0]
        if 'checksum' not in file_data:
            raise UploadFailedException('Could not extract checksum from response of uploaded data')

        import_data = {
            "id": 2,
            "method": "BaseForm.invoke",
            "params": [
                {
                    "javaClass": "no.tripletex.tcp.web.AccountingImportForm",
                    "documentationComponent": "154",
                    "system": "3",
                    "encoding": "UTF-8",
                    "upload": {
                        "name": file_data['name'],
                        "id": file_data['id'],
                        "revision": file_data['revision'],
                        "checksum": file_data['checksum'],
                        "clientId": "upload"
                    },
                    "file": '',
                    "generateVatPostings": True
                },
                "doImportVouchers"
            ]
        }

        r = self.request_post('https://tripletex.no/JSON-RPC?syncSystem=0&contextId=2845076', json=import_data)
        if r.status_code != 200:
            raise UploadFailedException("Unexpected return code from JSON-RPC when importing")

        if 'error' in r.json():
            raise UploadFailedException("Upload failed: %s" % r.json()['error'])

    def get_project_id(self, project_number):
        projects = self.get_project_list()
        project_id = None
        for project in projects:
            if project['number'] == project_number:
                project_id = project['id']
                break

        if not project_id:
            raise TripletexException("Could not locate project id of project %s" % project_number)

        return project_id


class TripletexException(Exception):
    pass


class LoginFailedException(TripletexException):
    pass


class NotLoggedInException(TripletexException):
    pass


class LedgerNumberFailed(TripletexException):
    pass


class UploadFailedException(TripletexException):
    pass


if __name__ == '__main__':
    tt = Tripletex()
    print("Testing Tripletex-connection:")
    num = tt.get_next_ledger_number(2015)
    print("Next ledger number: %d" % num)

    # tt.import_gbat10(open('bilag2.csv', 'r', encoding='iso-8859-1').read())
