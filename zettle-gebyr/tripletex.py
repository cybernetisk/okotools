import json
from types import SimpleNamespace
import requests
from requests.auth import HTTPBasicAuth


class Tripletex:
    def __init__(self, base_url, consumer_token, employee_token, expiration_date):
        self.base_url = base_url
        self.consumer_token = consumer_token
        self.employee_token = employee_token
        self.expiration_date = expiration_date
        self.session_token = self.create_session_token().value.token
        self.auth = self.authenticate(self.session_token)
        self.headers = {'Content-Type': 'application/json' }

    @classmethod
    def from_config(cls, config):
        return cls(config.base_url, config.consumer_token, config.employee_token, config.expiration_date)

    def create_session_token(self):
        params = {'consumerToken' : self.consumer_token, 'employeeToken' : self.employee_token, 'expirationDate' : self.expiration_date}
        r = requests.put(f'{self.base_url}/token/session/:create', params=params)
        if (r.status_code == 200):
            return self.map(r)
        else:
            print(r.status_code, r.text, r.reason)

    def authenticate(self, session_token):
        return HTTPBasicAuth('0', session_token)

    def who_am_i(self, fields=''):
        params = {'fields': fields}
        r = requests.get(f'{self.base_url}/token/session/>whoAmI', params=params, auth=self.auth)
        return self.map(r)

# ledger
    def create_voucher(self, payload):
        r = requests.post(f'{self.base_url}/ledger/voucher', data=json.dumps(payload), auth=self.auth, headers=self.headers)
        return self.map(r)

# account
    def get_accounts(self, fields=''):
        params = {'fields': fields}
        r = requests.get(
            f'{self.base_url}/ledger/account',
            params=params,
            auth=self.auth
            )
        return self.map(r)

# subscribe, see https://developer.tripletex.no/docs/documentation/webhooks/
    def list_available_subscriptions(self, fields=''):
        params = {'fields': fields}
        r = requests.get(
            f'{self.base_url}/event',
            params=params,
            auth=self.auth
            )
        return self.map(r)

    def list_subscriptions(self, fields=''):
        params = {'fields': fields}
        r = requests.get(
            f'{self.base_url}/event/subscription',
            params=params,
            auth=self.auth
            )
        return self.map(r)

    def subscribe_to_voucher_inbox(self, payload):
        # params = {'fields' : fields}
        r = requests.post(
            f'{self.base_url}/event/subscription',
            data=payload,
            auth=self.auth,
            headers=self.headers)
        return self.map(r)

# helpers
    @staticmethod
    def map(responce):
        data = json.dumps(responce.json())
        #print(json.dumps(responce.json(), indent=4, sort_keys=True, ensure_ascii=False))
        return json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
