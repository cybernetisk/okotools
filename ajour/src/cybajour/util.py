from enum import Enum
from pathlib import Path
from typing import List, Optional

import pandas
import pandas_access as mdb


class Database(Enum):
    CASHREGN = "Cashregn.mdb"
    CASHDATA = "Cashdata.mdb"
    DATAFLET = "DataFlet.mdb"
    MODULERX = "ModulerX.mdb"


class DatabaseCollection:
    def __init__(self, path: Path = Path.cwd()):
        self._paths = {
            Database.CASHREGN: path / Database.CASHREGN.value,
            Database.CASHDATA: path / Database.CASHDATA.value,
            Database.DATAFLET: path / Database.DATAFLET.value,
        }

    def __getitem__(self, database: Database):
        return self._paths[database]


class Col:
    def __init__(self, name: str, alias: str):
        self.name = name
        self.alias = alias


class DataSet:
    def __init__(
        self,
        dbcol: DatabaseCollection,
        database: Database,
        tablename: str,
        columns: Optional[List[Col]] = None
    ):
        self.dbcol = dbcol
        self.database = database
        self.tablename = tablename
        self.columns = columns

    def df(self):
        data = mdb.read_table(
            str(self.dbcol[self.database]),
            self.tablename
        )

        if self.columns is not None:
            cols = [it.name for it in self.columns]
            data = data[cols]

        # Rename columns.
        if self.columns is not None:
            data.columns = [it.alias for it in self.columns]

        return data


def relative_path(name):
    return str(Path().cwd() / name)


def remove_onevalue_columns(data):
    cols = []
    for col in data.columns:
        if len(data[col].unique()) > 1:
            cols.append(col)
    return data[cols]


def find_latest_datadir(args):
    base = Path.cwd() / "data"

    if args == "":
        reports = sorted(base.glob("*Z"))
        if len(reports) == 0:
            print("No reports found in '{}'".format(base))
            return
        args = next(reversed(reports)).name

    datadir = base / args
    if not datadir.exists():
        raise ValueError("Not found: " + str(datadir))
    elif not datadir.is_dir():
        raise ValueError("Not a dir: " + str(datadir))

    return datadir
