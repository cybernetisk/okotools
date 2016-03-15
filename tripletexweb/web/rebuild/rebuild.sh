#!/bin/bash

printf "Content-Type: text/plain\r\n"
printf "\r\n"

export LANG=nb_NO.UTF-8

cd ../../../tripletex
source env/bin/activate
./export.py

