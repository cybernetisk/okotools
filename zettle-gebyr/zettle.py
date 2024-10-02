# zettle.py
import requests
from datetime import timedelta, datetime

class Zettle:
    def __init__(self, zettle_id, zettle_secret):
        self.zettle_id = zettle_id
        self.zettle_secret = zettle_secret
        self.token = self.get_zettle_token()

    def get_zettle_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'client_id': self.zettle_id,
            'assertion': self.zettle_secret
        }
        r = requests.post('https://oauth.zettle.com/token', headers=headers, data=data)

        if r.status_code == 200:
            return r.json().get('access_token')
        else:
            print("Failed to get Zettle token:", r.status_code, r.text, r.reason)
            return None

    def get_fees(self, start_date, end_date):
        if not self.token:
            print("No Zettle token available. Exiting get_fees.")
            return {}

        header = {'Authorization': 'Bearer ' + self.token}
        url_base = 'https://finance.izettle.com/v2/accounts/liquid/transactions'

        offset = 0
        limit = 1000
        fee_dict = {}
        total_fees = 0

        while True:
            url = (f"{url_base}?start={start_date}T04:00:00-00:00&end={end_date}T04:00:00-00:00"
                   f"&includeTransactionType=PAYMENT_FEE&limit={limit}&offset={offset}")

            r = requests.get(url, headers=header)

            if r.status_code != 200:
                print("Failed to get Zettle fees:", r.status_code, r.text, r.reason)
                break

            data = r.json()

            for transaction in data:
                timestamp = transaction['timestamp'][0:10]
                hour = int(transaction['timestamp'][11:13])
                if hour < 4:
                    date_format = '%Y-%m-%d'
                    timestamp = (datetime.strptime(timestamp, date_format).date() - timedelta(days=1)).strftime(date_format)

                amount = transaction['amount'] / 100
                if timestamp in fee_dict:
                    fee_dict[timestamp] += amount
                else:
                    fee_dict[timestamp] = amount
                total_fees += amount

            offset += limit
            if len(data) < 1000:
                break

        return fee_dict
