from typing import List, Optional, TypedDict

# Created by looking at https://tripletex.no/v2/swagger.json
# Fields we are not interested in are left out.


class Department(TypedDict):
    id: int
    name: str
    departmentNumber: str
    displayName: str
    isInactive: Optional[bool]


class ListResponseDepartment(TypedDict):
    # fullResultSize: int
    # from: int
    count: int
    versionDigest: str
    values: List[Department]


class Account(TypedDict):
    id: int
    number: int
    name: str
    description: Optional[str]
    type: Optional[str]
    isInactive: Optional[bool]


class ListResponseAccount(TypedDict):
    values: List[Account]


class MainProject(TypedDict):
    id: int
    number: Optional[str]


class Project(TypedDict):
    id: int
    name: str
    number: Optional[str]
    displayName: Optional[str]
    startDate: str
    endDate: Optional[str]
    mainProject: Optional[MainProject]


class ListResponseProject(TypedDict):
    values: List[Project]


class PostingAccount(TypedDict):
    number: int
    name: str


class PostingDepartment(TypedDict):
    id: int
    name: str
    departmentNumber: Optional[str]


class PostingVoucher(TypedDict):
    number: int
    description: str
    year: int


class PostingProject(TypedDict):
    id: int
    number: Optional[str]
    name: str


class Posting(TypedDict):
    id: int
    account: PostingAccount
    amount: float
    date: str
    department: PostingDepartment
    description: Optional[str]
    voucher: PostingVoucher
    project: PostingProject


class ListResponsePosting(TypedDict):
    count: int
    values: List[Posting]
