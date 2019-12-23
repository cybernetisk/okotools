from pathlib import Path
from typing import List, Optional

import pandas

import pyodbc


class Col:
    def __init__(self, name: str, alias: str):
        self.name = name
        self.alias = alias


class DataSet:
    def __init__(
        self,
        filename: str,
        tablename: str,
        columns: Optional[List[Col]] = None
    ):
        self.filename = filename
        self.tablename = tablename
        self.columns = columns

    def df(self):
        cnxn = connect(self.filename)

        cols = "*"
        if self.columns is not None:
            cols = ', '.join([it.name for it in self.columns])

        data = pandas.read_sql(f"SELECT {cols} FROM {self.tablename}", cnxn)
        cnxn.close()

        # Rename columns.
        if self.columns is not None:
            data.columns = [it.alias for it in self.columns]

        return data


def table_info(cnxn, table_name):
    print(f"Showing details about {table_name}")

    # https://github.com/mkleehammer/pyodbc/wiki/Cursor
    cursor = cnxn.cursor()
    for col in cursor.columns(table_name):
        print("{:25s} {:^15s} {:10s}".format(
            col.column_name,
            col.type_name,
            "NULLABLE" if col.nullable else ""
        ))


def relative_path(name):
    return str(Path().cwd() / name)


def connect(name):
    dbpath = relative_path(name)
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={dbpath};'
    )
    cnxn = pyodbc.connect(conn_str)
    return cnxn


def table_data(cnxn, name):
    data = pandas.read_sql(f"SELECT * FROM {name}", cnxn)
    return data


def get_table_names(cnxn):
    cursor = cnxn.cursor()
    return [r.table_name for r in cursor.tables(tableType='TABLE')]


def remove_onevalue_columns(data):
    cols = []
    for col in data.columns:
        if len(data[col].unique()) > 1:
            cols.append(col)
    return data[cols]
