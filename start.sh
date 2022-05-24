#!/bin/bash

date_year=`date |cut -d ' ' -f6`
date_month=`date |cut -d ' ' -f2`
date_day=`date |cut -d ' ' -f3`
full_date="$date_year"_"$date_month"_"$date_day"
./runserver.py > /var/log/inod/web_log_"$full_date".txt 2>&1 &
./inod_send.py > /var/log/inod/send_log_"$full_date".txt 2>&1 &
./inod_read.py > /var/log/inod/read_log_"$full_date".txt 2>&1 &
