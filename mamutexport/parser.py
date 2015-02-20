#!/bin/env python
# -*- coding: utf-8 -*-
import csv
import re

fieldnames = ["accid", "accdesc", "regdate", "transid", "lineno", "maindesc", "data59", "data14", "data15", "data57", "contid", "custvendid", "invoid", "vatnumber", "period", "debet", "kredit", "saldo", "contname", "prosjekt", "avdeling", "inngåendesaldo", "inngåendesaldodebet", "inngåendesaldokredit", "utgåendesaldo", "utgåendesaldodebet", "utgåendesaldokredit", "akkumulertsaldo"]

f = open('MAMUT32.TXT', 'rb')
#reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_NONNUMERIC)
reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_ALL)

# år: {semester: {avdeling: {prosjekt: {kontonr: verdi}}}}
newdata = {}

for row in reader:
    d = re.split(':| |\\.', row['regdate'])

    year = d[2]
    if int(d[1]) <= 6:
        sem = 'Vår'
    else:
        sem = 'Høst'

    avd = unicode(row['avdeling'], 'latin-1').encode('utf-8')
    if avd == '(Ingen)':
        avd = ''

    prosj = unicode(row['prosjekt'], 'latin-1').encode('utf-8')
    account = int(row['accid'])
    amount = row['saldo']

    if account < 3000:
        ## ikke bruk avdeling og prosjekt på balanse
        #prosj = ''
        #avd = ''
        continue

    if year not in newdata:
        newdata[year] = {}
    if sem not in newdata[year]:
        newdata[year][sem] = {}
    if avd not in newdata[year][sem]:
        newdata[year][sem][avd] = {}
    if prosj not in newdata[year][sem][avd]:
        newdata[year][sem][avd][prosj] = {}
    if account not in newdata[year][sem][avd][prosj]:
        newdata[year][sem][avd][prosj][account] = 0

    newdata[year][sem][avd][prosj][account] += float(amount.replace(",", "."))


f2 = open('result.csv', 'w')
w = csv.writer(f2, delimiter=',', quoting=csv.QUOTE_ALL)

w.writerow(["Konto", "Spesifisering", "Avdeling", "Prosjekt", "Type", "År", "Semester", "Beløp"])

for year in newdata:
    for sem in newdata[year]:
        for avd in newdata[year][sem]:
            for prosj in newdata[year][sem][avd]:
                for account in sorted(newdata[year][sem][avd][prosj]):
                    amount = str(newdata[year][sem][avd][prosj][account]).replace(".", ",")
                    w.writerow([account, "", avd, prosj, "Regnskap", year, sem, amount])

f.close()
f2.close()

print "Sjekk result.csv!"
