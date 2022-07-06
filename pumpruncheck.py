#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
from datetime import datetime
import datetime
import time
import pymysql #MySQL 연결 위한 라이브러리
import logging

# 로그 생성
logger = logging.getLogger()

# 로그의 출력 기준 설정
logger.setLevel(logging.INFO)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# log를 파일에 출력
file_handler = logging.FileHandler('my.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#중지 명령이거나 카운터 값이 모두 처리된경우 자동모드를 종료하여야 한다.
def clear_runflage(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = 'UPDATE sensoractiveconfig SET runflage = 0, runcount = 0, countmode = 0 WHERE sensorid = {0}'.format(sensorid)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
        
#카운터 값을 하나씩 뺀다
def degree_count(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = 'UPDATE sensoractiveconfig SET runcount = runcount - 1 WHERE sensorid = {0}'.format(sensorid)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
        
# 대기 시간과 배기 시간 동안은 대기 해야 하는 부분이 있으므로
# 무한 모드일때 runflage 3 -> 1, runtimecheck는 데이터를 읽은 다음 업데이트를 하도록 했다.
# 한정 모드일때 runflage 3 -> 1, runcount 를 빼준다. runcount가 0인 경우는 runflage=0로
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

            if rows == 1: # 하나의 센서만 돌고 있는 경우
                if result[0][3] == 1: # 무한 모드
                    sensorid = result[0][0]
                    sql = "UPDATE sensoractiveconfig A,  SET runflage = 1 WHERE sensorid={0}".format(sensorid)
                if result[0][2] > 0 and result[0][3] == 0: # 한정 모드, 카운터가 0 아닌 경우 카운터 삭감
                    sensorid = result[0][0]
                    sql = "UPDATE sensoractiveconfig SET runflage = 1, runcount = runcount -1 WHERE runcount > 0 and sensorid={0}".format(sensorid)
                if result[0][2] == 0 and result[0][3] == 0: # 한정 모드, 카운터가 0인 경우 초기화 하도록
                    sensorid = result[0][0]
                    sql = "UPDATE sensoractiveconfig SET runflage = 0 WHERE runcount = 0 and sensorid={0}".format(sensorid)
                curs.execute(sql)
                db.commit()
                db.close()
                finish_update(sensorid)
            if rows > 1: # 여러개의 센서
                for i in range(0, rows):
                    if result[i][3] == 1: # 무한모드
                        sensorid = result[i][0]
                        sql = "UPDATE sensoractiveconfig SET runflage = 1 WHERE sensorid={0}".format(sensorid)
                    if result[i][2] > 0 and result[i][3] == 0: # 한정 모드, 카운터가 0 아닌 경우 카운터 삭감
                        sensorid = result[i][0]
                        sql = "UPDATE sensoractiveconfig SET runflage = 1, runcount = runcount -1 WHERE runcount > 0 and sensorid={0}".format(sensorid)
                    if result[i][2] == 0 and result[i][3] == 0: # 한정 모드, 카운터가 0인 경우 초기화 하도록
                        sensorid = result[i][0]
                        sql = "UPDATE sensoractiveconfig SET runflage = 0 WHERE runcount = 0 and sensorid={0}".format(sensorid)
                    curs.execute(sql)
                    db.commit()
                    db.close()
                    finish_update(sensorid)
    finally:
        msg = "Pump running time finished.."
        logger.info('Steps: %s',msg )
        

#최종 완료했다는 프래그
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
        
#대기 시간과 배기 시간 동안은 대기 해야 하는 부분이 있으므로
#sensoractiveconfig에 등록된 펌프 동작시간을 1초단위로 뺀다.
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