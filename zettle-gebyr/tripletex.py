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
        self.session_token = None
        self.auth = None
        
        self.create_session()
        self.authenticate(self.session_token)

    def create_session(self):
        url = f"{self.base_url}/token/session/:create"
        params = {
            'consumerToken': self.consumer_token,
            'employeeToken': self.employee_token,
            'expirationDate': self.expiration_date
        }

        response = requests.put(url, params=params)
        if response.status_code == 200:
            self.session_token = self.map(response).value.token
            print("Session token created successfully:", self.session_token)
        else:
            print("Failed to create session token:", response.status_code, response.text)
    
    def authenticate(self, session_token):
        self.auth = HTTPBasicAuth('0', session_token)

    def create_voucher(self, payload):
        if not self.session_token:
            print("No session token available, cannot create voucher.")
            return

        url = f"{self.base_url}/ledger/voucher"
        headers = {
            'Authorization': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, auth=self.auth, headers=headers)
        if response.status_code == 201:
            return response.json()
        else:
            return {
                'status_code': response.status_code,
                'text': response.text
            }

# helpers
    @staticmethod
    def map(response):
        data = json.dumps(response.json())
        #print(json.dumps(responce.json(), indent=4, sort_keys=True, ensure_ascii=False))
        return json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
