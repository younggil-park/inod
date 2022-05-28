#!/bin/bash

stop_target=`ps -ef |grep python |grep "runserver.py" |awk '{print$2}'`
for each_target in $stop_target; do
    kill -9 $each_target
done

stop_target=`ps -ef |grep python |grep "inod_send.py" |awk '{print$2}'`
for each_target in $stop_target; do
    kill -9 $each_target
done

stop_target=`ps -ef |grep python |grep "inod_read.py" |awk '{print$2}'`
for each_target in $stop_target; do
    kill -9 $each_target
done
#stop_target_count=`netstat -nlpt |grep python |grep ":5005" |wc -l`
#stop_target=`netstat -nlpt |grep python |grep ":5005" |awk '{print $7}' |cut -d '/' -f1`
#kill -9 $stop_target

