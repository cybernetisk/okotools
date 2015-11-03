#!/usr/bin/env python3

# pip3 install requests cookielib

import requests
import http
import urllib
import re

# settings are stored in settings.py, example:
# username = "username"
# password = "password"
from settings import *


class TripletexBase():
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

    def get_login_data(self):
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
    def get_url_ledger(self, year):
        """year = 2015"""
        return 'https://tripletex.no/execute/viewJournal?javaClass=no.tripletex.tcp.web.JournalForm&documentationComponent=145&contextId=2845076&isExpandedFilter=true&period.startDate=%d-01-01&period.endOfPeriodDate=%d-12-31&period.periodType=1&=%d&registeredById=-1&updatedById=-1&numberSeriesId=89077&startNumber=&endNumber=&accountId=-1&minAmountString=&maxAmountString=&amountType=2&ascending=false&rowCount=2&act=content&scope=ajaxContent' % (year, year, year)

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

    def import_gbat10(self, data):
        if not isinstance(data, str):
            raise ValueError("Need a unicode string as GBAT10-data")

        files = [('file', ('bilag.csv', data.encode('utf-8'), 'text/plain')), ]
        r = self.request_post('https://tripletex.no/execute/uploadCentral?contextId=2845076', files=files)
        #[{"id":"29027318","revision":"1","name":"bilag.csv","size":"0","readableSize":"0","uid":"0","checksum":"da39a3ee5e6b4b0d3255bfef95601890afd80709"}]

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
                    "file": "",
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

    #tt.import_gbat10(open('bilag2.csv', 'r', encoding='iso-8859-1').read())
