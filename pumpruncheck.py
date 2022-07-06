#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
from datetime import datetime
import datetime
import time
import pymysql #MySQL ���� ���� ���̺귯��
import logging

# �α� ����
logger = logging.getLogger()

# �α��� ��� ���� ����
logger.setLevel(logging.INFO)

# log ��� ����
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log ���
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# log�� ���Ͽ� ���
file_handler = logging.FileHandler('my.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#���� ����̰ų� ī���� ���� ��� ó���Ȱ�� �ڵ���带 �����Ͽ��� �Ѵ�.
def clear_runflage(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = 'UPDATE sensoractiveconfig SET runflage = 0, runcount = 0, countmode = 0 WHERE sensorid = {0}'.format(sensorid)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
        
#ī���� ���� �ϳ��� ����
def degree_count(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = 'UPDATE sensoractiveconfig SET runcount = runcount - 1 WHERE sensorid = {0}'.format(sensorid)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
        
# ��� �ð��� ��� �ð� ������ ��� �ؾ� �ϴ� �κ��� �����Ƿ�
# ���� ����϶� runflage 3 -> 1, runtimecheck�� �����͸� ���� ���� ������Ʈ�� �ϵ��� �ߴ�.
# ���� ����϶� runflage 3 -> 1, runcount �� ���ش�. runcount�� 0�� ���� runflage=0��
def check_pumptime():
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "SELECT sensorid, runtimecheck, runcount, countmode FROM sensoractiveconfig WHERE runflage = 3 and runtimecheck = 0"
            curs.execute(sql)
            rows = curs.rowcount
            result = list(curs.fetchall())
            msg = "result={0}".format(result)
            logger.info('get_cmdprocess: %s',msg )

            if rows == 1: # �ϳ��� ������ ���� �ִ� ���
                if result[0][3] == 1: # ���� ���
                    sensorid = result[0][0]
                    sql = "UPDATE sensoractiveconfig A,  SET runflage = 1 WHERE sensorid={0}".format(sensorid)
                if result[0][2] > 0 and result[0][3] == 0: # ���� ���, ī���Ͱ� 0 �ƴ� ��� ī���� �谨
                    sensorid = result[0][0]
                    sql = "UPDATE sensoractiveconfig SET runflage = 1, runcount = runcount -1 WHERE runcount > 0 and sensorid={0}".format(sensorid)
                if result[0][2] == 0 and result[0][3] == 0: # ���� ���, ī���Ͱ� 0�� ��� �ʱ�ȭ �ϵ���
                    sensorid = result[0][0]
                    sql = "UPDATE sensoractiveconfig SET runflage = 0 WHERE runcount = 0 and sensorid={0}".format(sensorid)
                curs.execute(sql)
                db.commit()
                db.close()
                finish_update(sensorid)
            if rows > 1: # �������� ����
                for i in range(0, rows):
                    if result[i][3] == 1: # ���Ѹ��
                        sensorid = result[i][0]
                        sql = "UPDATE sensoractiveconfig SET runflage = 1 WHERE sensorid={0}".format(sensorid)
                    if result[i][2] > 0 and result[i][3] == 0: # ���� ���, ī���Ͱ� 0 �ƴ� ��� ī���� �谨
                        sensorid = result[i][0]
                        sql = "UPDATE sensoractiveconfig SET runflage = 1, runcount = runcount -1 WHERE runcount > 0 and sensorid={0}".format(sensorid)
                    if result[i][2] == 0 and result[i][3] == 0: # ���� ���, ī���Ͱ� 0�� ��� �ʱ�ȭ �ϵ���
                        sensorid = result[i][0]
                        sql = "UPDATE sensoractiveconfig SET runflage = 0 WHERE runcount = 0 and sensorid={0}".format(sensorid)
                    curs.execute(sql)
                    db.commit()
                    db.close()
                    finish_update(sensorid)
    finally:
        msg = "Pump running time finished.."
        logger.info('Steps: %s',msg )
        

#���� �Ϸ��ߴٴ� ������
def finish_update(sensorid):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs: 
            sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets SET A.f_flag = 1, A.f_time = '{0}', B.s_flag=3, B.s_time = '{0}' WHERE A.sensorid={1} and B.sensorid={1} and A.r_flag=1 and B.s_flag=2 and A.cmd=B.cmd ".format(nowtime, sensorid)
            curs.execute(sql)
            db.commit()
            
    finally:
        db.close()
        
#��� �ð��� ��� �ð� ������ ��� �ؾ� �ϴ� �κ��� �����Ƿ�
#sensoractiveconfig�� ��ϵ� ���� ���۽ð��� 1�ʴ����� ����.
def degree_pumptime():
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "UPDATE sensoractiveconfig SET runtimecheck = runtimecheck - 1 WHERE runflage = 3 and runtimecheck > 0"
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
    
def main():
    degree_pumptime()
    check_pumptime()
        
if __name__ == "__main__":
    logger.info('This program is an Pump Running Check program after read data.' )
    while True:
        try:
            main()
        except KeyboardInterrupt:
            sys.exit()
        time.sleep(1)