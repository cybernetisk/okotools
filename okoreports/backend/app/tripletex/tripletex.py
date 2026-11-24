from __future__ import annotations

import base64
import datetime
import logging
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple, TypedDict, Union

import requests

from tripletex._api_types import (ListResponseAccount, ListResponseDepartment,
                                  ListResponsePosting, ListResponseProject)
from tripletex._api_types import Posting as ApiPosting

logger = logging.getLogger(__name__)


def raise_for_status_pretty(response: requests.Response):
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"Response: {response.content}")
        raise TripletexException(f"HTTP Error: {str(e)}") from e


@dataclass
class Project:
    id: int
    number: Optional[int]
    text: str
    start: str  # YYYY-MM-DD
    end: Optional[str]  # YYYY-MM-DD
    parent: Optional[int]  # reference to id


@dataclass
class Account:
    id: int
    text: str
    group: Optional[str]
    active: bool


@dataclass
class Posting:
    date: datetime.date
    description: Optional[str]
    amount: float
    voucher_number: int
    voucher_year: int
    voucher_description: Optional[str]
    department_name: Optional[str]
    department_number: Optional[int]
    account_name: str
    account_number: int
    project_id: Optional[int]
    project_name: Optional[str]
    project_number: Optional[int]


@dataclass
class Department:
    id: int
    number: int
    name: str


PostingAggregateLeaf = TypedDict("PostingAggregateLeaf", {
    "in": int,
    "out": int,
})


class PostingAggregateNode(TypedDict):
    meta: Any
    data: PostingAggregate


PostingAggregate = Union[
    PostingAggregateLeaf,
    Dict[str, PostingAggregateNode]
]


class TripletexConnectorV2:
    """
    This class has the support role of communicating with Tripletex.
    """

    def __init__(self, customer_token: str, employee_token: str):
        self.customer_token = customer_token
        self.employee_token = employee_token
        self.session_token_cache: Optional[Tuple(datetime.date, str)] = None

    @staticmethod
    def _compute_expiration_date() -> datetime.date:
        return datetime.date.today() + datetime.timedelta(days=2)

    def _authorization_header_value(self) -> str:
        session_token = self._get_session_token()
        basic_value = base64.b64encode(f"0:{session_token}".encode("utf-8")).decode("utf-8")
        return "Basic {}".format(basic_value)

    def _get_session_token(self) -> str:
        expiration_date = self._compute_expiration_date()

        if self.session_token_cache is None or self.session_token_cache[0] != expiration_date:
            self.session_token_cache = (expiration_date, self._create_session_token(expiration_date))

        return self.session_token_cache[1]

    def _create_session_token(self, expiration_date) -> str:
        logger.info("Creating session token")

        url = f"https://tripletex.no/v2/token/session/:create?consumerToken={self.customer_token}&employeeToken={self.employee_token}&expirationDate={expiration_date}"
        response = requests.request("PUT", url)
        raise_for_status_pretty(response)

        return response.json()["value"]["token"]

    def call_api(self, method: str, path: str, *args, **kwargs) -> requests.Response:
        headers = kwargs.get("headers", {}).copy()
        headers["authorization"] = self._authorization_header_value()

        url = f"https://tripletex.no/v2{path}"

        return requests.request(method, url, *args, **kwargs, headers=headers)


class Tripletex:
    def __init__(self, context_id: int, connector: TripletexConnectorV2):
        self.context_id = context_id
        self.connector = connector

    def _get_all_postings(self, date_start: str, date_to: str, account_start: int, account_end: int) -> list[ApiPosting]:
        result = []
        from_ = 0
        max_page_size = 10000
        fields = "id,account(number,name),amount,date,department(id,name,departmentNumber),description,voucher(number,description,year),project(id,number,name)"

        # Have a limit just in case the pagination stops working.
        max_iter = 10
        while True:
            response = self.connector.call_api("GET", f"/ledger/posting?dateFrom={date_start}&dateTo={date_to}&accountNumberFrom={account_start}&accountNumberTo={account_end}&count={max_page_size}&from={from_}&fields={fields}")
            raise_for_status_pretty(response)

            page_data: ListResponsePosting = response.json()
            this_count = page_data["count"]
            from_ += this_count
            result.extend(page_data["values"])

            if this_count < max_page_size:
                break

            max_iter -= 1
            if max_iter == 0:
                raise TripletexException("Too many iterations to fetch data from Tripletex")

            logger.info("Fetching next page of ledger items")

        return result

    def get_postings(self, date_start: str, date_to: str, account_start: Optional[int] = None, account_end: Optional[int] = None) -> list[Posting]:
        items = self._get_all_postings(date_start=date_start, date_to=date_to, account_start=account_start or 0, account_end=account_end or 9999)

        def none_for_empty(value: Optional[str]):
            if value == "":
                return None
            return value

        def str_to_int(value: Optional[str]):
            if value is not None:
                return int(value)

        result: list[Posting] = []
        for row in items:
            id = row['id']

            voucher = row['voucher']
            if voucher is None:
                raise ValueError(f"Missing voucher for posting {id}")

            account = row['account']
            if account is None:
                raise ValueError(f"Missing account for posting {id}")

            project = row['project']

            result.append(Posting(
                date=datetime.date.fromisoformat(row["date"]),
                description=row['description'],
                amount=float(row['amount']),
                voucher_number=voucher['number'],
                voucher_year=voucher['year'],
                voucher_description=none_for_empty(voucher['description']),
                department_name=none_for_empty(row['department']['name']) if row['department'] is not None else None,
                department_number=str_to_int(none_for_empty(row['department']['departmentNumber'])) if row['department'] is not None else None,
                account_name=account['name'],
                account_number=account['number'],
                project_id=project['id'] if project else None,
                project_name=project['name'] if project else None,
                project_number=str_to_int(project['number']) if project else None,
            ))

        return result

    @staticmethod
    def aggregate_postings(postings: list[Posting], *aggregators: Callable[[Posting], Union[bool, Tuple[str, Any]]]) -> PostingAggregate:
        result = OrderedDict()
        default_data = {'in': 0, 'out': 0}

        for row in postings:
            # perform aggregators and check if it filters the row out
            intermediates = []
            for aggregator in aggregators:
                res = aggregator(row)  # should return either False, True or (key, meta)
                if res is False:
                    break
                if res is not True:
                    intermediates.append(res)

            else:
                level = result
                for key, meta in intermediates:
                    if key not in level:
                        level[key] = {'meta': meta, 'data': OrderedDict()}
                    level = level[key]['data']

                if level == OrderedDict():
                    level.update(default_data)

                if row.account_number < 4000 or row.account_number in [8050, 8072]:
                    level['in'] = round(level['in'] + row.amount, 2)
                else:
                    level['out'] = round(level['out'] + row.amount, 2)

        return result

    def get_departments(self) -> list[Department]:
        response = self.connector.call_api("GET", "/department?count=10000")
        raise_for_status_pretty(response)

        data: ListResponseDepartment = response.json()

        department_list: list[Department] = []

        for department in data['values']:
            # Not sure if we really want to skip these.
            # Maybe add details as a field and include?
            if department.get("isInactive", False):
                continue

            department_list.append(Department(
                id=department['id'],
                number=int(department['departmentNumber']),
                name=department['name'],
            ))

        return department_list

    def get_accounts(self) -> list[Account]:
        response = self.connector.call_api("GET", "/ledger/account?count=10000")
        raise_for_status_pretty(response)
        data: ListResponseAccount = response.json()

        account_list: list[Account] = []

        for account in data["values"]:
            account_list.append(Account(
                id=account["number"],
                text=account["name"],
                group=account["type"],
                active=not account.get("isInactive", False),
            ))

        return account_list

    def get_projects(self) -> list[Project]:
        response = self.connector.call_api("GET", "/project?count=10000")
        raise_for_status_pretty(response)
        data: ListResponseProject = response.json()

        project_list: list[Project] = []

        for project in data["values"]:
            main_project = project.get("mainProject", None)
            display_name = project["displayName"]

            project_list.append(Project(
                id=project["id"],
                number=int(project["number"]) if project["number"] is not None else None,
                text=display_name if display_name is not None else project["name"],
                start=project["startDate"],
                end=project["endDate"],
                parent=main_project["id"] if main_project is not None else None,
            ))

        return project_list

    @staticmethod
    def get_project_id(projects: list[Project], project_number: int) -> int:
        project_id = None
        for project in projects:
            if project.number == project_number:
                project_id = project.id
                break

        if not project_id:
            raise TripletexException("Could not locate project id of project %s" % project_number)

        return project_id


class TripletexException(Exception):
    pass


class LoginFailedException(TripletexException):
    pass


class NotLoggedInException(TripletexException):
    pass


class LedgerNumberFailed(TripletexException):
    pass


class UploadFailedException(TripletexException):
    def __init__(self, message, response=None):
        super(UploadFailedException, self).__init__(message)
        self.response = response
