import logging
from pprint import pformat
from typing import Tuple

import pytest

from tripletex import settings
from tripletex.tripletex import (
    TripletexConnectorV2,
    Tripletex,
    Posting,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def connector():
    return TripletexConnectorV2(credentials_provider=settings.credentials_provider)


@pytest.fixture(scope="class")
def tripletex(connector):
    return Tripletex(settings.context_id, connector=connector)


class TestTripletex:
    def test_get_departments(self, tripletex):
        logger.info("Getting departments")
        result = tripletex.get_departments()
        logger.info(f"Found {len(result)} items")
        logger.info(pformat(result))

    def test_get_accounts(self, tripletex):
        logger.info("Getting accounts")
        result = tripletex.get_accounts()
        logger.info(f"Found {len(result)} items")
        logger.info(pformat(result))

    def test_get_projects(self, tripletex):
        logger.info("Getting projects")
        result = tripletex.get_projects()
        logger.info(f"Found {len(result)} items")
        logger.info(pformat(result))

    def test_get_postings(self, tripletex):
        logger.info("Getting postings")
        result = tripletex.get_postings(date_start="2020-01-01", date_to="2023-01-01", account_start=None)
        logger.info(f"Found {len(result)} items - showing first 10")
        logger.info(pformat(result[0:10]))

    def test_aggregate_postings(self, tripletex):
        postings = tripletex.get_postings(date_start="2022-01-01", date_to="2022-02-01", account_start=3000)

        def group_by_account_number(row: Posting) -> Tuple[str, str]:
            return (
                str(row.account_number),
                row.account_name,
            )

        def group_by_project_number(row: Posting) -> Tuple[str, str]:
            return (
                str(row.project_number) if row.project_number is not None else "",
                row.project_name,
            )

        result = tripletex.aggregate_postings(
            postings,
            group_by_project_number,
            group_by_account_number,
        )

        logger.info(pformat(result))
