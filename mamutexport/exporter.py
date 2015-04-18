#!/bin/env python
# -*- coding: utf-8 -*-
import csv
import pymssql

server = "localhost:49313"
database = "Client00010001"


def writedata(data):
    f2 = open('result.csv', 'w')
    w = csv.writer(f2, delimiter=',', quoting=csv.QUOTE_ALL)
    w.writerow(["Konto", "Spesifisering", "Avdeling", "Prosjekt", "Type", "År", "Semester", "Beløp"])

    for row in data:
        amount = str(row['amount']).replace(".", ",")
        w.writerow([
            row['account'],
            "",
            row['avd'],
            row['prosj'],
            "Regnskap",
            row['year'],
            row['sem'],
            amount])

    f2.close()
    print("Sjekk result.csv!")


def getsqldata():
    conn = pymssql.connect(server, database=database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            l.ACCID,
            dbo.Sys_GetAvdeling(l.DATA15) avdeling,
            p.TASK_NAME prosjekt,
            b.ACCYEAR,
            IIF(MONTH(b.REGDATE) <= 6, 'Vår', 'Høst'),
            SUM(l.CURRENCYSUM)
        FROM
            G_MAIN b
            INNER JOIN G_MAINL l ON l.MAINID = b.MAINID
            LEFT JOIN G_PROJ p ON l.DATA14 = p.PROJID
        WHERE b.STATUSID = 3 AND l.ACCID >= 3000
        GROUP BY l.ACCID, b.ACCYEAR,
            dbo.Sys_GetAvdeling(l.DATA15),
            IIF(MONTH(b.REGDATE) <= 6, 'Vår', 'Høst'),
            p.TASK_NAME
        HAVING SUM(l.CURRENCYSUM) != 0
        ORDER BY p.TASK_NAME, b.ACCYEAR, l.ACCID
        """)

    data = []
    for row in cursor:
        avd = row[1].strip() if row[1] != "(Ingen)" else None
        prosj = row[2].strip() if row[2] is not None else None
        data.append({
            'account': row[0].strip(),
            'avd': avd,
            'prosj': prosj,
            'year': row[3],
            'sem': row[4],
            'amount': row[5]})

    conn.close()

    return data


if __name__ == '__main__':
    writedata(getsqldata())
