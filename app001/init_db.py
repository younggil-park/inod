#-*- coding:utf-8 -*-

import re
from app001 import app
from app001.models import User
import bcrypt
import datetime
import time
import sys
import struct
import pymysql #MySQL 연결 위한 라이브러리
import csv
import logging
from app001 import thread_sensor

# database 초기화하고 새로 생성하는 함수
def init_database():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
	
    create_sensordata_query = "CREATE TABLE sensordata (chkCount bigint(26) NOT NULL, sensorID int(11) NOT NULL, H2 varchar(20) NOT NULL, H2S varchar(20) NOT NULL, NH3 varchar(20) NOT NULL, Toluene varchar(20) NOT NULL, CO2 varchar(20) NOT NULL, VOC varchar(20) NOT NULL, CO varchar(20) NOT NULL, Temp1 varchar(10) NOT NULL, Temp2 varchar(10) NOT NULL, Hum1 varchar(10) NOT NULL, Hum2 varchar(10) NOT NULL, InputDateTime datetime NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8"
    
    create_pumprunntime_query = "CREATE TABLE pumprunntime (nos int(11) NOT NULL, injections varchar(6) NOT NULL, fittimes varchar(6) NOT NULL, exjections varchar(6) NOT NULL, dates timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() ) ENGINE=InnoDB DEFAULT CHARSET=utf32"
    
    create_pumprunntime_query = "INSERT INTO pumprunntime (nos, injections, fittimes, exjections, dates) VALUES (0, '10', '10', '10', '2021-10-20 03:21:53'), (1, '10', '10', '10', '2021-10-20 03:21:53'),(2, '10', '10', '10', '2021-10-20 03:21:53'),(3, '10', '10', '10', '2021-10-20 03:21:53'),(4, '10', '10', '10', '2021-10-20 03:21:53')"
    
    with db.cursor() as curs:
        curs.execute(create_pumprunntime_query)
        db.commit()
        curs.execute(create_pumprunntime_query)
        db.commit()

    

    db.close()