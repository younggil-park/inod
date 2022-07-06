#-*- coding:utf-8 -*-
from datetime import datetime
import datetime
from app001 import app
import logging
import time
import pymysql #MySQL 연결 위한 라이브러리

'''
서버요청  명령    데이터 수신 및 응답      센서 결과에 대한 서버응답
센싱      )     데이터 97자리          1
로그      +     데이터 97자리          1
로그      +      2 로그없음
로그      +      3 SD불량
배기      ,      2
흡기      -      2
값설정     W      2
흡입시간   I      I
교정시간   P      P
배기시간   E      없음
재시작     R     없음
'''
#==============================================================================================
# 메인 home 화면에 최근 센싱 데이터 출력 위해서 디비 쿼리
def get_sensortb():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    sensordatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT sensorid, h2, h2s, nh3, toluene, co2, voc, co, temp1, temp2, hum1, hum2 FROM sensordata  ORDER BY chkcount DESC LIMIT 1"
            curs.execute(sql)
            #한번 호출할때마다 하나의 row 레코드만 갖고온다
            sensordatatb = curs.fetchone()
            if sensordatatb == None:
                sensordatatb = [0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    finally:
        db.close()
        return sensordatatb

# ro 값 읽기
def get_rotb():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rodatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT sensorname, ro_value FROM calrovalue"
            curs.execute(sql)
            #한번 호출할때 전체 row 레코드 갖고온다
            rodatatb = curs.fetchall()
    finally:
        return rodatatb
        db.close()

# scope 값 읽기
def get_scopetb():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    scopedatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT sensorname, level, x_side, y_side, scope FROM calscopevalue"
            curs.execute(sql)
            scopedatatb = curs.fetchall()
    finally:
        return scopedatatb
        db.close()
        
# run time 값 읽기
def get_runtimetb():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    runtimetb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT intaketimes, fittimes, exhausttimes FROM sensorpumpruntime"
            curs.execute(sql)
            runtimetb = curs.fetchall()
    finally:
        return runtimetb
        db.close()

#==============================================================================================
        
def action_config(mode, *args):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    curs = db.cursor()
    
    if mode == "autorun": #무한 반복 펌프 동작 유무, 동작 중지 프래그는 0으로 처리
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET runflage = 1, runcount = {0}, countmode = {1} WHERE sensorid = {2}'.format(args[1],args[3], i)
            curs.execute(sql)
            db.commit()
    if mode == "runstop": #무한 반복 펌프 동작 중지 하면 sensoractiveconfig SET runflage = 0, runcount = 0으로 업데이터한다.
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET runflage = 0, runcount = 0, countmode = 0 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
            
            # 티켓 처리 부분과 cmd처리 부분을 모두 완료로 업데이트한다.
            sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON (A.tickets = B.tickets) SET A.s_flag = 1, A.s_time = {0}, A.r_flag = 1, r.f_time = {0}, A.f_flag = 1, A.f_time = {0}, B.s_flag=3 WHERE A.sensorid={1} and B.sensorid={1} and A.cmd=B.cmd".format(nowtime, sensorid)
            curs.execute(sql)
            db.commit()
            
    if mode == "sd_read": #SD카드에서 데이터 읽기
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET sdreadflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "exhaust": #배기 펌프 동작
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET exhaustflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "intake":  #흡기 펌프 동작
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET intakeflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "pumpruntime":  #펌프 동작 시간 설정
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET runtimeflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
            args = list(args[1])
            sql = 'UPDATE sensorpumpruntime SET intaketimes = {0}, fittimes = {1}, exhausttimes = {2}, checkflage = 1 WHERE sensorid = {3}'.format(args[0], args[1], args[2], i)
            msg = 'pumpruntime sql {0}'.format(sql)
            app.logger.info(msg)
            curs.execute(sql)
            db.commit()
    if mode == "pumpreset":  #펌프 재시작
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET resetflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "roconfig":  #ro 값 변경, cal_ro_tb 테이블에는 데이터 존재
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET roflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "scopeconfig":  #scope 값 변경, cal_scope_tb 테이블에는 데이터 존재
        for i in args[0]:
            sql = 'UPDATE sensoractiveconfig SET scopeflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
            
    db.close()
    
#===========================================================================================
# 설정 정보를 저장하는 함수들

# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
def config_ro_value(sensor_ids, ro1, ro2, ro3, ro4):
    ro_value = ro1,ro2,ro3,ro4
    i = 0
    sample_data = +00.000
    
    # RO백업
    save_RO_Scope_Backup(1)
    for sensor_id in range(0, len(sensor_ids)):
        i = 0
        for items in range(5, 9):
            app.logger.info(' Ro Send=%s', ro_value[i])
            # Save RO or Calibration VALUES calibrationtb(RO 혹은 scope 선택, 센서이름(MQ135~138), RO값 또는 Calibration값)
            save_RO_Calbration(items, float(ro_value[i]))
            i += 1
    
# 기울기값 변경 요청: idx1, W(대문자),5(6|7|8),0(1|2|3),X절편,Y절편,기울기,etx)-32자리
def config_scope_value(sensor_ids,scop0, scop1, scop2, scop3):
    scope_level_0= scop0.split(';') #135 센서의 모든것 
    scope_level_1= scop1.split(';') #136
    scope_level_2= scop2.split(';') #137
    scope_level_3= scop3.split(';') #138
    scope_list = scope_level_0,scope_level_1,scope_level_2,scope_level_3

    # Scope백업
    save_RO_Scope_Backup(2)
    for sensor_id in range(0, len(sensor_ids)): 
        for sensorname in range(0,4):
            for level in range(0,4):
                scop1 = scope_list[sensorname][level].split(',')
                save_Scope_Calbration(sensorname, level, float(scop1[0]), float(scop1[1]), float(scop1[2]))
                app.logger.info('scope send data %s',scop1)
    
#RO 및 Scope 보정 작업하기 전에 백업 수행        
def save_RO_Scope_Backup(mode):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    nowtime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    try:
        if mode == 1:
            curs = db.cursor()
            backtbname = "calrovalue_{0}".format(nowtime)
            sql = "CREATE TABLE  `{0}`  SELECT * FROM calrovalue".format(backtbname)
            curs.execute(sql)
            db.commit()
        if mode == 2:
            curs = db.cursor()
            backtbname = "calscopevalue_{0}".format(nowtime)
            sql = "CREATE TABLE `{0}`  SELECT * FROM calscopevalue".format(backtbname)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
        
# Save RO VALUES calibrationtb(센서이름(MQ135~138), RO값)
def save_RO_Calbration(sensorname, value):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    nowtime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    try:
        curs = db.cursor()
        sensorname = 'MQ13{0}'.format(sensorname)
        sql = "UPDATE calrovalue SET ro_value = '{0}', checkdate = '{1}' WHERE sensorname='{2}'".format(value, nowtime, sensorname)
        curs.execute(sql)
        db.commit()
        
    finally:
        db.close()

# Save Scope Calibration VALUES calibrationtb(scope 선택, 센서이름(MQ135~138), scope Calibration값)
# (sensorname,level,float(scop1[0]),float(scop1[1]),float(scop1[2]))
def save_Scope_Calbration(sensorname, level, value1, value2, value3):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    nowtime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    try:
        curs = db.cursor()
        sensorname = 'MQ13{0}'.format(sensorname)
        sql = "UPDATE calscopevalue SET x_side = '{0}', y_side = '{1}', scope = '{2}', checkdate = '{3}' WHERE sensorname='{4}' and level={5}".format(value1, value2, value3, nowtime, sensorname, level)
        curs.execute(sql)
        db.commit()
    finally:
        db.close()

#===========================================================================================        
# 데이터베이스 관련 함수 목록 사작        
#로그 저장 
def SaveLog(auto_send_cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    #app.logger.info('1-3.SaveLog %s',auto_send_cmd)
    try:
        with db.cursor() as curs:
            curs.execute("INSERT INTO sensorlog  (commands, inputdatetime) VALUES (%s,%s)", (auto_send_cmd,nowtime))
        db.commit()
    finally:
        db.close()