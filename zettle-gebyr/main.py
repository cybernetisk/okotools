import sys
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from calendar import monthrange
from tripletex import Tripletex
from tripletex_config import Tripletex_Config
from zettle import Zettle
from zettle_config import Zettle_Config


def month(date):
    date_format = '%Y-%m-%d'
    month = datetime.strftime(datetime.strptime(date,date_format),"%B").lower()
    translate = {
        "january": "januar",
        "february": "februar",
        "march": "mars",
        "april": "april",
        "may": "mai",
        "june": "june",
        "july": "juli",
        "august": "august",
        "september": "september",
        "october": "oktober",
        "november": "november",
        "december": "desember"
    }
    if month in translate.keys():
        return translate[month]
    return False


def auto_dates():
    date_now = datetime.now(ZoneInfo("Europe/Oslo")).date()  # for automatic
    year = date_now.year
    month = date_now.month
    days_in_month = monthrange(year, month)[1]
    this_date = (date_now).strftime('%Y-%m-%d')[0:7]
    next_date = (date_now + timedelta(days=days_in_month)).strftime('%Y-%m-%d')[0:7]
    from_date = f'{this_date}-01'
    to_date = f'{next_date}-01'
    return from_date, to_date


def manual_dates(manual_date):
    date_format = '%Y-%m-%d'
    date_now = datetime.strptime(manual_date, date_format).date()
    year = date_now.year
    month = date_now.month
    days_in_month = monthrange(year, month)[1]
    this_date = (date_now).strftime('%Y-%m-%d')[0:7]
    next_date = (date_now + timedelta(days=days_in_month)).strftime('%Y-%m-%d')[0:7]
    from_date = f'{this_date}-01'
    to_date = f'{next_date}-01'
    return from_date, to_date


def payload(tripletex_client, fee_dict):

    postings_list = []
    row_num = 1

    for date in fee_dict:
        fee_sum = fee_dict[date]
        posting = {
            "row": row_num,
            "date": date,
            "description": "Daglig gebyr Zettle",
            "amountGross": -fee_sum,
            "amountGrossCurrency": -fee_sum,
            "account": {
                "id": 15311097
                }
            }
        contra_posting = {
            "row": row_num,
            "date": date,
            "description": "Daglig gebyr Zettle",
            "amountGross": fee_sum,
            "amountGrossCurrency": fee_sum,
            "account": {
                "id": 57458194
                }
            }
        postings_list.append(posting)
        postings_list.append(contra_posting)
        desc_date = datetime.now(ZoneInfo("Europe/Oslo")).strftime('%Y-%m-%d')
        desc_text = "Gebyr Zettle " + month(postings_list[0]["date"])
        row_num += 1

    ret = {
        "date": desc_date,
        "description": desc_text,
        "postings": postings_list
        }

    return ret


def main():
    date1 = 0
    date2 = 0
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg == "auto":
            date1, date2 = auto_dates()
        else:
            date1, date2 = manual_dates(arg)
    else:
        print("Usage manual: python main.py 2022-01-01")
        print("Usage auto  : python main.py auto")
        return

    zettle_config = Zettle_Config()
    tripletex_config = Tripletex_Config()

    zettle_client = Zettle(
        zettle_config.zettle_id,
        zettle_config.zettle_secret
        )
    fee_dict = zettle_client.get_fees(date1, date2)

    tripletex_client = Tripletex(
        tripletex_config.base_url,
        tripletex_config.consumer_token,
        tripletex_config.employee_token,
        tripletex_config.expiration_date
        )
    tripletex_client.create_voucher(payload(tripletex_client, fee_dict))

    print('Finished - check tripletex journal')


if __name__ == '__main__':
    main()
