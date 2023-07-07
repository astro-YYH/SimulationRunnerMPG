#!/bin/bash

current_datetime=$(date "+%Y-%m-%d %H:%M:%S")
echo "Current date and time: $current_datetime"

python single_test_Neff.py

current_datetime=$(date "+%Y-%m-%d %H:%M:%S")
echo "Current date and time: $current_datetime"