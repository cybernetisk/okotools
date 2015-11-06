#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def get_num(val):
    if val is None:
        return 0
    try:
        return int(val)
    except ValueError:
        return 0
