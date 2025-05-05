import os
import sys
from datetime import datetime, timedelta
from calendar import monthrange
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from zettle import Zettle
from tripletex import Tripletex

load_dotenv()

def parse_custom_dates(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    return start_date, end_date

def auto_dates():
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
    last_day_of_month = monthrange(now.year, now.month)[1]
    end_date = datetime(now.year, now.month, last_day_of_month).strftime("%Y-%m-%d")
    return start_date, end_date

def manual_dates(manual_date):
    date = datetime.strptime(manual_date, "%Y-%m-%d")
    start_date = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
    last_day_of_month = monthrange(date.year, date.month)[1]
    end_date = datetime(date.year, date.month, last_day_of_month).strftime("%Y-%m-%d")
    return start_date, end_date

def month(date):
    date_format = '%Y-%m-%d'
    month = datetime.strftime(datetime.strptime(date,date_format),"%B").lower()
    translate = {
        "january": "januar",
        "february": "februar",
        "march": "mars",
        "april": "april",
        "may": "mai",
        "june": "juni",
        "july": "juli",
        "august": "august",
        "september": "september",
        "october": "oktober",
        "november": "november",
        "december": "desember"
    }
    return translate.get(month, month)

def payload(fee_dict):
    postings_list = []
    row_num = 1

    for date, fee_sum in fee_dict.items():
        posting = {
            "row": row_num,
            "date": date,
            "description": "Daglig gebyr Zettle",
            "amountGross": -fee_sum,
            "amountGrossCurrency": -fee_sum,
            "account": {"id": 15311097}
        }
        contra_posting = {
            "row": row_num,
            "date": date,
            "description": "Daglig gebyr Zettle",
            "amountGross": fee_sum,
            "amountGrossCurrency": fee_sum,
            "account": {"id": 57458194}
        }
        postings_list.append(posting)
        postings_list.append(contra_posting)
        row_num += 1

    description_date = datetime.now(ZoneInfo("Europe/Oslo")).strftime('%Y-%m-%d')
    description_text = "Gebyr Zettle " + month(postings_list[0]["date"])

    return {
        "date": description_date,
        "description": description_text,
        "postings": postings_list
    }

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "auto":
        start_date, end_date = auto_dates()
    elif len(sys.argv) == 2 and sys.argv[1] != "auto":
        start_date, end_date = manual_dates(sys.argv[1])
    elif len(sys.argv) == 3:
        start_date, end_date = parse_custom_dates(sys.argv[1], sys.argv[2])
    else:
        print("syntax: <filename.py> auto or <filename.py> yyyy-mm-dd or <filename.py> startdate enddate")
        exit()

    print("Program running...")
    
    current_time = datetime.now()
    if datetime.strptime(end_date, "%Y-%m-%d") > current_time:
        print(f"end_date must be before the {current_time} since it otherwise makes problems in the accounting software")
        exit()


    zettle_client = Zettle(os.getenv("ZETTLE_ID"), os.getenv("ZETTLE_SECRET"))
    fee_dict = zettle_client.get_fees(start_date, end_date)
    print(f"Retrieved Zettle fees from {start_date} to {end_date}: {fee_dict}")

    tripletex_base_url = os.getenv("TRIPLETEX_BASE_URL", "https://api.tripletex.io/v2")
    tripletex_consumer_token = os.getenv("TRIPLETEX_CONSUMER_TOKEN")
    tripletex_employee_token = os.getenv("TRIPLETEX_EMPLOYEE_TOKEN")

    if not tripletex_consumer_token or not tripletex_employee_token:
        print("Missing Tripletex tokens. Exiting...")
        return

    expiration_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    tripletex_client = Tripletex(
        tripletex_base_url,
        tripletex_consumer_token,
        tripletex_employee_token,
        expiration_date  # Future date
    )

    if not tripletex_client.session_token:
        print("Unable to create Tripletex client. Exiting...")
        return

    voucher_payload = payload(fee_dict)
    response = tripletex_client.create_voucher(voucher_payload)
    print(f"Completed: {response}")

if __name__ == "__main__":
    main()
