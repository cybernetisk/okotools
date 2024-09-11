import requests
import json
from datetime import datetime, timedelta


class Zettle:

    def __init__(self, zettle_id, zettle_secret):
        self.zettle_id = zettle_id
        self.zettle_secret = zettle_secret
        self.session_token = self.get_zettle_token()

    def get_zettle_token(self):

        params = {
                  'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                  'client_id': self.zettle_id,
                  'assertion': self.zettle_secret
                }
        r = requests.post('https://oauth.zettle.com/token', params)

        if r.status_code == 200:
            return r.json()['access_token']
        else:
            print(r.status_code, r.text, r.reason)

    def get_fees(self,startdate, enddate):

        header = {'Authorization': 'Bearer ' + self.session_token}
        url_base = 'https://finance.izettle.com/v2/accounts/liquid/transactions'

        offset = 0      # start get() at offset xx
        limit = 1000    # maximum transactions to fetch per get(). Zettle supports up to 1000
        fee_dict = {}   # this is where the day:fee will be stored
        total_fees = 0

        while(True):

            url = url_base + '?start=' + str(startdate) + 'T04:00:00-00:00&end=' + str(enddate) + 'T04:00:00-00:00&includeTransactionType=PAYMENT_FEE&limit=' + str(limit) + '&offset=' + str(offset)

            r = requests.get(url, headers=header)

            if r.status_code == 200:
                data = r.json()
            else:
                print(r.status_code, r.text, r.reason)

            timestamp = data[0]['timestamp'][0:10]

            for transaction in data:

                timestamp = transaction['timestamp'][0:10]
                hour = int(transaction['timestamp'][11:13])
                if(hour < 4):  # transactions registered at zettle between 00.00 and 05.00 (Norway +1 hour offset)
                    date_format = '%Y-%m-%d'
                    timestamp = datetime.strftime(datetime.strptime(timestamp, date_format).date() - timedelta(days=1),date_format)
                if timestamp in fee_dict.keys():                        # adds fee from transaction to sum of fees for day
                    fee_dict[timestamp] += transaction['amount']/100
                else:                                                   # adds new day with fees to datastructure
                    fee_dict[timestamp] = transaction['amount']/100
                    total_fees += transaction['amount']

            offset += limit
            if len(data) < 1000:  # no more transactions to fetch, since the last request retrieved below maximum of 1000
                break

        return fee_dict
