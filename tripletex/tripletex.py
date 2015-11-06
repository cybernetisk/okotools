#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tripletex.tripletex import TripletexImporter

if __name__ == '__main__':
    tt = TripletexImporter()
    print("Testing Tripletex-connection:")
    num = tt.get_next_ledger_number(2015)
    print("Next ledger number: %d" % num)

    # tt.import_gbat10(open('bilag2.csv', 'r', encoding='iso-8859-1').read())
