import csv
import math
import re
import sys
from pathlib import Path
from pprint import pprint
from typing import List


class Trans:
    def __init__(self, posting_date, interest_date, description, amount):
        self.posting_date = posting_date
        self.interest_date = interest_date
        self.description = description
        self.amount = amount

    @property
    def is_negative(self):
        return self.amount.startswith("-")


def group_all_trans(data: str) -> List[str]:
    # Split the data in a way we do not loose any transactions
    # we might not properly format. We want the script to fail
    # for these scenarios, rather than us silently missing them.
    data = re.sub(r"^(\d{4} .+ \d{4} )", r"--SPLIT--\1", data, flags=re.MULTILINE)

    all_trans = []
    for item in data.split("--SPLIT--"):
        item = item.strip()
        if item != "":
            all_trans.append(item)

    return all_trans


def guess_is_amount_in(description: str) -> bool:
    return (
        description.startswith("Overførsel")
        or description.startswith("Omsetning bank axept")
        or description.startswith("Renter")
        # Covering "Straksinnbetaling" and possibly others.
        or ("innbetaling" in description and "Fra" in description)
        or (description.startswith("Giro") and "Fra" in description)
        or description.startswith("Innskuddsautomat")
        or (description.startswith("Kontoregulering") and "Fra" in description)
    )


def format_desc(parts: List[str]) -> str:
    result = " ".join(parts)
    result = re.sub(r"^([^,]+)(,.+ Id \d+) (.+)( Buntnr)", r"\1 \3\2\4", result)
    return result


def parse_single_trans(data: str, year: int):
    # 1 = posting date (ex 1001 for 1st October)
    # 2 = description part 1
    # 3 = interest date (ex 1001 for 1st October)
    # 4 = amount (ex 12.345,67)
    # 5 = description part 2

    m = re.match(r"^(\d{4}) (.+?) (\d{4}) ([\d\.,]+)((\n)(.+))?$", data, re.DOTALL)
    if m is None:
        raise Exception("Failed to parse: " + data)

    descriptions = [m.group(2)]
    if m.group(7) is not None:
        descriptions.extend(m.group(7).split("\n"))

    description = format_desc(descriptions)
    amount = m.group(4).replace(".", "").replace(",", ".")

    if not guess_is_amount_in(description):
        amount = "-" + amount

    return Trans(
        posting_date="{}.{}.{}".format(m.group(1)[2:], m.group(1)[0:2], year),
        interest_date="{}.{}.{}".format(m.group(3)[2:], m.group(3)[0:2], year),
        description=description,
        amount=amount,
    )


def parse_trans(data: str, year: int):
    return [parse_single_trans(item, year) for item in group_all_trans(data)]


def format_num(value: str) -> str:
    return value.replace(".", ",")


def remove_delimiter(value: str) -> str:
    """
    Tripletex does not seem to support quoted fields, so we cannot include
    the delimiter character as data. We replace it will comma so it is
    almost the same.
    """
    return value.replace(";", ",")


def convert(out, data: str, year: int, open_amount, close_amount):
    parsed_trans = parse_trans(data, year)

    diff = 0
    for trans in parsed_trans:
        diff += float(trans.amount)

    calculated_close_amount = round(float(open_amount) + diff, 2)
    if not math.isclose(calculated_close_amount, float(close_amount)):
        diff = round(calculated_close_amount - float(close_amount), 2)
        print(
            "Calculated close amount ({}) was expected to be ({}). Diff: {}".format(
                calculated_close_amount, close_amount, diff
            )
        )
        sys.exit(1)

    writer = csv.writer(out, delimiter=";", lineterminator="\n", quoting=csv.QUOTE_NONE)
    writer.writerows(
        [
            ["Konto", "Kontonavn"],
            ["", ""],
            ["Inngående saldo", "Utgående saldo"],
            [format_num(open_amount), format_num(close_amount)],
            ["Bokført dato", "Forklarende tekst", "Inn", "Ut"],
            *[
                [
                    trans.posting_date,
                    remove_delimiter(trans.description),
                    format_num(trans.amount) if not trans.is_negative else "",
                    format_num(trans.amount) if trans.is_negative else "",
                ]
                for trans in parsed_trans
            ],
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Syntax: {} <input-file> <year> <start-amount> <end-amount>".format(
                sys.argv[0]
            )
        )
        sys.exit(1)

    out_file = "out.csv"
    print("Will write to " + out_file)

    data = Path(sys.argv[1]).read_text(encoding="utf-8")

    with open(out_file, "w", encoding="iso-8859-1") as f:
        convert(f, data, int(sys.argv[2]), sys.argv[3], sys.argv[4])
