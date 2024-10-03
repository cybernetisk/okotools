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

    def upload_file(self, file_content, filename='document.pdf', description=None, split=False):
        upload_url = f"{self.base_url}/ledger/voucher/importDocument?split={str(split).lower()}"
        headers = {'Authorization': f'Bearer {self.session_token}'}
        files = {
            'file': (filename, file_content, 'application/pdf')
        }
        data = {
            'description': description or filename
        }

        response = requests.post(upload_url, auth=self.auth, headers=headers, files=files, data=data)

        if response.status_code == 201:
            print(f"Successfully uploaded {filename} to Tripletex.")
            print(f"Response: {response.json()}")
            return response.status_code
        else:
            print(f"Failed to upload {filename} to Tripletex. Status code: {response.status_code}, Response: {response.text}")
            return response.status_code

    # helpers
    @staticmethod
    def map(response):
        data = json.dumps(response.json())
        return json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
