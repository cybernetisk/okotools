import requests
from requests.auth import HTTPBasicAuth
import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def obtain_token():
    token_url = "https://authorization.nettskjema.no/oauth2/token"
    client_id = os.getenv('API_CLIENT_ID')
    client_secret = os.getenv('API_SECRET')

    if not client_id or not client_secret:
        raise ValueError("API_CLIENT_ID or API_SECRET not found in environment variables")

    data = {
        'grant_type': 'client_credentials',
    }

    try:
        response = requests.post(token_url, data=data, auth=HTTPBasicAuth(client_id, client_secret))
        response.raise_for_status()
        token_data = response.json()
        if 'access_token' not in token_data or 'expires_in' not in token_data:
            raise ValueError("Invalid token response")

        token_data['expires_at'] = datetime.datetime.now().timestamp() + token_data['expires_in']
        return token_data
    except requests.RequestException as e:
        raise SystemExit(e)

def save_token(token_data):
    with open('token.json', 'w') as f:
        json.dump(token_data, f)

def load_token():
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
            return token_data
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def check_and_refresh_token():
    token_data = load_token()

    if not token_data:
        print("Token not found, obtaining a new one.")
        return obtain_and_save_new_token()

    now = datetime.datetime.now().timestamp()
    expires_at = token_data.get('expires_at', 0)

    if now >= expires_at:
        print("Token expired. Obtaining a new token...")
        return obtain_and_save_new_token()
    else:
        print("Token valid.")
        return token_data

def obtain_and_save_new_token():
    token_data = obtain_token()
    save_token(token_data)
    return token_data

def parse_xndjson(xndjson_str):
    if not xndjson_str.strip():
        return []

    lines = xndjson_str.strip().split("\n")

    parsed_lines = []
    for line in lines:
        try:
            parsed_lines.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"Error decoding line: {line}")

    return parsed_lines

def api_request(url, method='GET', data=None, params=None, timeout=300):
    token_data = check_and_refresh_token()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    try:
        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        raise SystemExit(f"API request failed: {e}")

    content_type = response.headers.get('Content-Type', '')
    if 'application/json' in content_type:
        return response.json()
    elif 'application/x-ndjson' in content_type:
        return parse_xndjson(response.text)
    else:
        return response

# Endpoint-specific functions
def get_form_info(form_id):
    url = f"https://nettskjema.no/api/v3/form/{form_id}/info"
    return api_request(url)

def get_form_submissions(form_id):
    url = f"https://nettskjema.no/api/v3/form/{form_id}/answers"
    return api_request(url)

def create_submission(form_id, submission_data):
    url = f"https://nettskjema.no/api/v3/form/{form_id}/submission"
    return api_request(url, method='POST', data=submission_data)

def delete_submissions(form_id, submission_data):
    url = f"https://nettskjema.no/api/v3/form/{form_id}/submission"
    return api_request(url, method="DELETE", data=submission_data)

def update_codebook(form_id, codebook_data):
    url = f"https://nettskjema.no/api/v3/form/{form_id}/codebook"
    return api_request(url, method='PUT', data=codebook_data)

def get_user_info():
    url = "https://nettskjema.no/api/v3/me"
    return api_request(url)

def get_submission_pdf(submission_id):
    url = f"https://nettskjema.no/api/v3/form/submission/{submission_id}/pdf"
    return api_request(url)

def get_submission_attachment(attachment_id):
    url = f"https://nettskjema.no/api/v3/form/submission/attachment/{attachment_id}"
    return api_request(url)
