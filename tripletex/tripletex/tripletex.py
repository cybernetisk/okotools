#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime
import requests
import http.cookiejar
import json
import urllib.parse
import html
import re
import getpass
from bs4 import BeautifulSoup
from collections import OrderedDict


class TripletexConnector:
    """
    This class has the support role of communicating with Tripletex
    """
    default_object = None

    def __init__(self, cookies_file=None, credentials_provider=None):
        if cookies_file is None:
            cookies_file = "/tmp/tripletex-cookies-%s.txt" % getpass.getuser()
        self.session = None
        self.cookies_file = cookies_file
        self.credentials_provider = credentials_provider if credentials_provider else self.default_credentials_provider

    @staticmethod
    def get_default_object():
        if not TripletexConnector.default_object:
            TripletexConnector.default_object = TripletexConnector()
        return TripletexConnector.default_object

    @staticmethod
    def default_credentials_provider():
        print('Må logge inn på Tripletex. Fyll inn brukernavn og passord som det skal logges inn med:')
        return (input('Brukernavn: '),
                getpass.getpass('Passord: '))

    def get_session_object(self):
        if self.session is not None:
            return self.session

        cj = http.cookiejar.MozillaCookieJar(self.cookies_file)
        try:
            cj.load(ignore_discard=True)
        except FileNotFoundError:
            pass

        self.session = requests.Session()
        self.session.cookies = cj

        return self.session

    @staticmethod
    def is_401(request):
        if request.status_code == 401:
            return True

        if request.status_code == 200 and request.headers['Content-Type'].lower().find('application/json') != -1:
            # tripletex don't always return valid json, and not always 401 neither
            parsed = json.loads(request.text.replace("'", '"'))
            try:
                if parsed['error']['javaClass'] == 'no.tripletex.common.exception.NotLoggedInException':
                    return True
            except KeyError:
                pass

        return False

    def force_user_logged_in(self, request, session, *args, **kwargs):
        if self.is_401(request):
            self.do_login()
            request = session.get(*args, **kwargs)
            if self.is_401(request):
                raise NotLoggedInException(request.text)
        return request

    def request_get(self, *args, **kwargs):
        s = self.get_session_object()
        r = s.get(*args, **kwargs)

        r = self.force_user_logged_in(r, s, *args, **kwargs)

        s.cookies.save(ignore_discard=True)
        return r

    def request_post(self, *args, **kwargs):
        s = self.get_session_object()
        r = s.post(*args, **kwargs)

        r = self.force_user_logged_in(r, s, *args, **kwargs)

        s.cookies.save()
        return r

    @staticmethod
    def get_login_data(credentials_provider):
        credentials = credentials_provider()

        return 'username=%s&password=%s&act=login&contentUrl=&site=no&recaptcha=false' % (
            urllib.parse.quote(credentials[0]), urllib.parse.quote(credentials[1]))

    def do_login(self):
        r = self.get_session_object().post('https://tripletex.no/execute/login',
                                           data=self.get_login_data(self.credentials_provider),
                                           headers={'content-type': 'application/x-www-form-urlencoded'},
                                           allow_redirects=False)

        if r.status_code != 302:
            raise LoginFailedException(r.text)


class TripletexBase:
    def __init__(self, contextId, connector=None):
        self.contextId = contextId
        self.connector = connector if connector else TripletexConnector.get_default_object()


class TripletexLedger(TripletexBase):
    def get_ledger(self, date_start, date_end, account_start=3000, account_end=""):
        q = OrderedDict()
        q['javaClass'] = "no.tripletex.tcp.web.LedgerForm"
        q['documentationComponent'] = "144"
        q['contextId'] = self.contextId
        q['isExpandedFilter'] = "true"
        q['onlyOpenPostings'] = "false"
        q['period.startDate'] = date_start  # "2016-01-01"
        q['period.endOfPeriodDate'] = date_end  # "2016-12-31"
        q['period.periodType'] = "1"
        q['openPostingsDateBefore'] = ""
        q['accountId'] = "-1"
        q['startNumber'] = account_start
        q['endNumber'] = account_end
        q['selectedCustomerId'] = "-1"
        q['selectedVendorId'] = "-1"
        q['selectedEmployeeId'] = "-1"
        q['selectedDepartmentId'] = "-1"
        q['selectedProjectId'] = "-1"
        q['includeSubProjectsOfSelectedProject'] = "false"
        q['selectedProductId'] = "-1"
        q['selectedVatId'] = "-1"
        q['minAmountString'] = ""
        q['maxAmountString'] = ""
        q['amountType'] = "2"
        q['orderBy'] = "1"
        q['postingCount'] = "500000"  # this field is not respected anyways
        q['viewCustomer'] = "true"
        q['viewVendor'] = "true"
        q['viewEmployee'] = "false"
        q['viewDepartment'] = "false"
        q['viewProject'] = "false"
        q['viewProduct'] = "false"
        q['csv'] = "true"
        q['csvHeader'] = "true"
        q['csvEncoding'] = "UTF-8"
        q['csvSeparator'] = ";"
        q['csvQualifier'] = '"'
        q['csvDecimal'] = "."
        q['csvLineBreak'] = "\n"

        query_string = urllib.parse.urlencode(q)
        url = "https://tripletex.no/execute/ledger?" + query_string

        r = self.connector.request_get(url)
        if r.status_code != 200:
            raise TripletexException("Could not fetch ledger, error code: %s" % r.status_code)

        result_list = []
        column_list = []

        fields_interested = [
            'Avdelingsnavn',
            'Avdelingsnummer',
            'Beløp',
            'Beskrivelse',
            'Bilagsbeskrivelse',
            'Bilagsnummer',
            'Bilagsår',
            'Dato',
            'Kontonavn',
            'Kontonummer',
            'Kundenavn',
            'Kundenummer',
            'Leverandørnavn',
            'Leverandørnummer',
            'Prosjektnavn',
            'Prosjektnummer',
        ]

        csvobj = csv.reader(r.text.strip().split('\n'), delimiter=';')
        is_first = True
        for row in csvobj:
            if is_first:
                for col in row:
                    column_list.append(col)
                is_first = False
                continue

            res = {}
            for i, col in enumerate(row):
                fieldname = column_list[i]
                if fieldname in fields_interested:
                    res[fieldname] = col

            # skip "Åpningsbalanse"
            if res['Bilagsnummer'] == '':
                continue

            # parse values
            res['Beløp'] = float(res['Beløp'])
            d = res['Dato'].split('-')
            res['Dato'] = datetime.date(int(d[0]), int(d[1]), int(d[2]))
            for field in ['Avdelingsnummer', 'Bilagsnummer', 'Bilagsår', 'Kontonummer',
                          'Kundenummer', 'Leverandørnummer', 'Prosjektnummer']:
                if res[field] == '':
                    res[field] = None
                else:
                    res[field] = int(res[field])

            result_list.append(res)

        return result_list

    def aggregate(self, ledgerdata, *aggregators):
        result = OrderedDict()
        default_data = {'in': 0, 'out': 0}

        for row in ledgerdata:
            # perform aggregators and check if it filters the row out
            intermediates = []
            for aggregator in aggregators:
                res = aggregator(row)  # should return either False, True or (key, meta)
                if res is False:
                    break
                if res is not True:
                    intermediates.append(res)

            else:
                level = result
                for key, meta in intermediates:
                    if key not in level:
                        level[key] = {'meta': meta, 'data': OrderedDict()}
                    level = level[key]['data']

                if level == OrderedDict():
                    level.update(default_data)

                if row['Kontonummer'] < 4000 or row['Kontonummer'] in [8050, 8072]:
                    level['in'] = round(level['in'] + row['Beløp'], 2)
                else:
                    level['out'] = round(level['out'] + row['Beløp'], 2)

        return result


class TripletexDepartments(TripletexBase):
    def get_department_list(self):
        url = "https://tripletex.no/JSON-RPC?syncSystem=0&contextId=" + str(self.contextId)

        post_data = {
            "marshallSpec": [
                "id",
                "number",
                "name",
                "nameAndNumber"
            ],
            "className": "JSONRpcClient.RequestExtraInfo",
            "id": 19,
            "method": "Department.searchForDepartments",
            "params": [
                self.contextId,
                '',
                1000,
                0
            ]
        }

        r = self.connector.request_post(url, json=post_data)
        if r.status_code != 200:
            raise TripletexException("Unexpected return code from JSON-RPC when fetching department list")

        if 'error' in r.json():
            raise TripletexException("Unexpected return value from JSON-RPC when fetching department list: %s" % r.json()['error'])

        department_list = []

        data = r.json()
        for department in data['result']:
            department_list.append({
                'id': department['id'],
                'number': department['number'],
                'name': department['name']
            })

        return department_list


class TripletexAccounts(TripletexBase):
    def get_accounts(self):
        url = "https://tripletex.no/execute/chartOfAccounts?act=content&scope=ui-id-2&contextId=" + str(self.contextId)
        r = self.connector.request_get(url)

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

    def get_report_result(self, date_start, date_end, project_id=None, include_sub_projects=False):
        q = OrderedDict()
        q['javaClass'] = "no.tripletex.tcp.web.ResultReport2Form"
        q['documentationComponent'] = "133"
        q['contextId'] = self.contextId
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

        r = self.connector.request_get(url)
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


class TripletexProjects(TripletexBase):
    def get_project_list_old(self):
        url = "https://tripletex.no/JSON-RPC?syncSystem=0&contextId=" + str(self.contextId)

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
                self.contextId,
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

        r = self.connector.request_post(url, json=post_data)
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
        q['contextId'] = self.contextId
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

        r = self.connector.request_get(url)
        if r.status_code != 200:
            raise TripletexException("Could not fetch project list")

        project_list = []
        for tr in re.findall(r'<tr.*?>(.+?)</tr>', r.text, re.DOTALL):
            tdlist = re.findall(r'<td.*?>(.+?)</td>', tr, re.DOTALL)

            if len(tdlist) > 7:
                project_id = re.search(r'projectId=(\d+)&', tdlist[1]).group(1)

                start_and_end = re.sub(r'<[^>]*?>', '', tdlist[5])
                m = re.match(r'^\s*(.+?)( (.+?))?\s*$', start_and_end)

                project_list.append({
                    'id': project_id,
                    'text': html.unescape(re.sub(r'  +', ' ', re.sub(r'<[^>]*?>', '', tdlist[2]).strip())),
                    'start': m.group(1),
                    'end': m.group(3)
                })

        return self.__project_list_find_parent(project_list)

    def get_report_projects(self, date_start, date_end, project_id=None, include_sub_projects=True):
        q = OrderedDict()
        q['javaClass'] = 'no.tripletex.tcp.web.ProjectResultReportForm'
        q['documentationComponent'] = '259'
        q['contextId'] = self.contextId
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

        r = self.connector.request_get(url)
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


class TripletexImporter(TripletexBase):
    @staticmethod
    def get_url_ledger(contextId, year):
        """year = 2015"""
        url = 'https://tripletex.no/execute/viewJournal?javaClass=no.tripletex.tcp.web.JournalForm&' + \
              'documentationComponent=145&contextId=%d&isExpandedFilter=true&period.startDate=%d-01-01&' + \
              'period.endOfPeriodDate=%d-12-31&period.periodType=1&=%d&registeredById=-1&updatedById=-1&' + \
              'numberSeriesId=89077&startNumber=&endNumber=&accountId=-1&minAmountString=&maxAmountString=&' + \
              'amountType=2&ascending=false&rowCount=2&act=content&scope=ajaxContent'
        return url % (contextId, year, year, year)

    def get_ledger(self, year):
        return self.connector.request_get(self.get_url_ledger(self.contextId, year))

    def get_next_ledger_number(self, year):
        data = self.get_ledger(year)

        m = re.search(r'Bilag nummer (\d+)-(\d+)', data.text)
        if m is None:
            raise LedgerNumberFailed(data.text)

        return int(m.group(1)) + 1

    def import_gbat10(self, data):
        if not isinstance(data, str):
            raise ValueError("Need a unicode string as GBAT10-data")

        files = [('file', ('bilag.csv', data.encode('utf-8'), 'text/plain')), ]
        r = self.connector.request_post('https://tripletex.no/execute/uploadCentral?contextId=' + str(self.contextId), files=files)
        # [{"id":"29027318","revision":"1","name":"bilag.csv","size":"0","readableSize":"0","uid":"0","checksum":"da39a3ee5e6b4b0d3255bfef95601890afd80709"}]

        if r.status_code != 200:
            raise UploadFailedException('Received unexpected status code %d when trying to upload' % r.status_code, r)

        file_data = r.json()[0]
        if 'checksum' not in file_data:
            raise UploadFailedException('Could not extract checksum from response of uploaded data', r)

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

        r = self.connector.request_post('https://tripletex.no/JSON-RPC?syncSystem=0&contextId=' + str(self.contextId),
                                        json=import_data)
        if r.status_code != 200:
            raise UploadFailedException("Unexpected return code from JSON-RPC when importing")

        if 'error' in r.json():
            raise UploadFailedException("Upload failed: %s" % r.json()['error'])


class TripletexException(Exception):
    pass


class LoginFailedException(TripletexException):
    pass


class NotLoggedInException(TripletexException):
    pass


class LedgerNumberFailed(TripletexException):
    pass


class UploadFailedException(TripletexException):
    def __init__(self, message, response=None):
        super(UploadFailedException, self).__init__(message)
        self.response = response
