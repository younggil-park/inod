#!/bin/bash

full_date=`date +%Y-%m-%d`
./runserver.py > /var/log/inod/web_log_"$full_date".txt 2>&1 &
./inod_send.py > /var/log/inod/send_log_"$full_date".txt 2>&1 &
./inod_read.py > /var/log/inod/read_log_"$full_date".txt 2>&1 &
./pumpruncheck.py > /var/log/inod/runcheck_log_"$full_date".txt 2>&1 &
