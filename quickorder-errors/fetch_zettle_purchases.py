import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import csv

# Load environment variables from .env file
load_dotenv()

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
            print("Token retrieved successfully.")
            return r.json().get('access_token')
        else:
            print(f"Failed to get Zettle token: {r.status_code}, {r.text}, {r.reason}")
            return None

    def fetch_purchases_by_month(self, year, month, folder_path='zettle_csv', limit=50):
        if not self.token:
            print("No token available. Exiting fetch_purchases.")
            return

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        start_date = datetime(year, month, 1).strftime('%Y-%m-%d')
        end_date = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')

        filename = f"purchases_{start_date}_to_{end_date}.csv"
        file_path = os.path.join(folder_path, filename)

        # Skip fetching if the file already exists
        if os.path.exists(file_path):
            print(f"File {filename} already exists. Skipping fetch.")
            return

        header = {'Authorization': f'Bearer {self.token}'}
        url = f"https://purchase.izettle.com/purchases/v2?limit={limit}&descending=true&startDate={start_date}&endDate={end_date}"

        purchases = []
        last_purchase_hash = None

        while True:
            request_url = url + (f'&lastPurchaseHash={last_purchase_hash}' if last_purchase_hash else '')
            print(f"Fetching URL: {request_url}")

            retries = 3
            attempt = 0
            while attempt < retries:
                try:
                    r = requests.get(request_url, headers=header, timeout=30)
                    print(f"Received response with status code: {r.status_code}")
                    if r.status_code == 200:
                        break
                    elif r.status_code == 504:
                        print("Gateway timeout occurred. Retrying...")
                        attempt += 1
                        time.sleep(5)
                    else:
                        print(r.text)
                        break
                except requests.exceptions.Timeout:
                    print("The request timed out. Retrying...")
                    attempt += 1
                    time.sleep(5)
                except requests.exceptions.RequestException as e:
                    print(f"An error occurred: {e}")
                    return

            if r.status_code != 200:
                print(f"Failed to fetch purchases: {r.status_code}, {r.text}")
                break

            data = r.json()
            retrieved_purchases = data.get('purchases', [])
            print(f"Fetched {len(retrieved_purchases)} purchases for {start_date} to {end_date}.")
            purchases.extend(retrieved_purchases)

            last_purchase_hash = data.get('lastPurchaseHash')
            if not last_purchase_hash:
                print("No more pages left to fetch.")
                break

        if purchases:
            self.save_purchases_to_csv(purchases, folder_path, start_date, end_date)

    def save_purchases_to_csv(self, purchases, folder_path, start_date, end_date):
        filename = f"purchases_{start_date}_to_{end_date}.csv"
        file_path = os.path.join(folder_path, filename)

        flattened_purchases = [self.flatten_dict(purchase) for purchase in purchases]
        all_keys = set(key for purchase in flattened_purchases for key in purchase.keys())

        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=sorted(all_keys))
            writer.writeheader()
            for purchase in flattened_purchases:
                writer.writerow(purchase)

        print(f"Purchases for {start_date} to {end_date} saved successfully.")

    def flatten_dict(self, d, parent_key='', sep='_'):
        items = {}
        if not isinstance(d, dict):
            print(f"Warning: Unexpected data type {type(d)} encountered during flattening.")
            return items

        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self.flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.update(self.flatten_dict(item, f"{new_key}_{i}", sep=sep))
            else:
                items[new_key] = v
        return items

# Define start and end year
start_year = 2022
end_year = 2026

print("Initializing Zettle client...")
zettle = Zettle(os.getenv("ZETTLE_ID"), os.getenv("ZETTLE_SECRET"))

if zettle.token:
    print(f"Bearer token: {zettle.token}")
else:
    print("Failed to retrieve a valid token.")
    exit()

for year in range(start_year, end_year):
    for month in range(1, 13):
        print(f"Starting to retrieve purchases for {year}-{month}...")
        zettle.fetch_purchases_by_month(year, month, limit=1000)

print("The script has finished executing.")
