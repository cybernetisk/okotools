import requests
from datetime import datetime, timedelta
import os
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

def encode_date(date):
    date_str = date.strftime('%Y-%m-%dT%H:%M:%S.000%z')
    date_str = date_str.replace(':', '%253A').replace('+', '%252B')
    return date_str

def get_csv_export(day, month, year, token, folder_path):
    start_date = datetime(year, month, day)
    end_date = start_date + timedelta(days=1)

    timezone_offset = '+0100'
    from_date = encode_date(start_date.replace(tzinfo=datetime.strptime(timezone_offset, '%z').tzinfo))
    to_date = encode_date(end_date.replace(tzinfo=datetime.strptime(timezone_offset, '%z').tzinfo))

    filename = f"export_{start_date.strftime('%Y_%m_%d')}.csv"
    file_path = os.path.join(folder_path, filename)
    
    if os.path.exists(file_path):
        print(f"File {filename} already exists. Skipping...")
        return

    url = f"https://api.quickorder.dk/v8/payments/csv-export?from_date={from_date}&to_date={to_date}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    }

    retries = 3
    delay = 5
    attempt = 0

    while attempt < retries:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                csv_url = data.get('url')
                if csv_url:
                    download_csv(csv_url, file_path)
                    return
                else:
                    print("CSV URL not found in the response. No data available to download.")
            else:
                handle_error(response)
                attempt += 1
                time.sleep(delay)
                
        except requests.exceptions.Timeout:
            print("The request timed out. Retrying...")
            attempt += 1
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            break

def handle_error(response):
    if response.status_code == 504:
        print("Gateway timeout occurred. Retrying...")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        print(f"Response: {response.text}")

def download_csv(csv_url, filename):
    try:
        response = requests.get(csv_url, timeout=10)
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            lines = csv_content.splitlines()
            
            # Check for content beyond headers
            if len(lines) > 1:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"CSV file downloaded successfully: {filename}")
            else:
                print(f"CSV contains only headers, skipping file creation for: {filename}")
        else:
            print(f"Failed to download CSV. Status code: {response.status_code}")
    except requests.exceptions.Timeout:
        print("The download request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the CSV: {e}")

def get_bearer_token(username, password):
    url = "https://pos-api.quickorder.io/public/tenants/3212/users/login"
    payload = {
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            token = data.get('x-amzn-remapped-authorization') or data.get('token')
            if not token:
                token = response.headers.get('x-amzn-remapped-authorization')
            if token:
                print("Bearer token retrieved successfully.")
                return token
            else:
                print("Bearer token not found.")
        else:
            print(f"Failed to retrieve token. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return None

def main():
    folder_path = 'csv'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    start_year = 2022
    end_year = 2026

    username = os.getenv('QUICKORDER_USERNAME')
    password = os.getenv('QUICKORDER_PASSWORD')
    bearer_token = get_bearer_token(username, password)

    if not bearer_token:
        print("Failed to get bearer token.")
        exit()

    tasks = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for year in range(start_year, end_year):
            for month in range(1, 13):
                days_in_month = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                for day in range(1, days_in_month.day + 1):
                    tasks.append(executor.submit(get_csv_export, day, month, year, bearer_token, folder_path))

        for future in as_completed(tasks):
            future.result()

    print("The script has finished executing.")

if __name__ == "__main__":
    main()
