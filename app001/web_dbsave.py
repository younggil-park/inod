from datetime import datetime
import datetime
from app001 import app
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
            sql = "SELECT sensorID, H2, H2S, NH3, Toluene, CO2, VOC, CO, Temp1, Temp2, Hum1, Hum2 FROM sensordata  ORDER BY chkCount DESC LIMIT 1"
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
            sql = "SELECT SensorName, RO_Value FROM cal_ro_tb"
            curs.execute(sql)
            #한번 호출할때 전체 row 레코드 갖고온다
            rodatatb = curs.fetchall()
    finally:
        db.close()
        return rodatatb
# scope 값 읽기
def get_scopetb():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    scopedatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT SensorName, level, X_side, Y_side, Scope FROM cal_scope_tb"
            curs.execute(sql)
            scopedatatb = curs.fetchall()
    finally:
        db.close()
        return scopedatatb
#==============================================================================================
        
def action_config(mode, *args):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    curs = db.cursor()
    if mode == "autorun": #무한 반복 펌프 동작 유무
        for i in agrs[1]:
            sql = 'UPDATE sensoractiveconfig SET runflage = {0} WHERE sensorid = {1}'.format(args[0],i)
            curs.execute(sql)
            db.commit()
     if mode == "runstop": #무한 반복 펌프 동작 중지
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET runstopflage = {0} WHERE sensorid = {1}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "sd_read": #SD카드에서 데이터 읽기
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET sdreadflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "exhaust": #배기 펌프 동작
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET exhaustflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "intake":  #흡기 펌프 동작
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET intakeflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "pumpruntime":  #펌프 동작 시간 설정
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET runtimeflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
            sql = 'UPDATE sensorpumpruntime SET intaketimes = {0}, fittimes = {1}, exhausttimes = {2}, checkflage = 1 WHERE sensorid = {3}'.format(agrs[1:0], agrs[1:1], agrs[1:2], i)
            curs.execute(sql)
            db.commit()
    if mode == "pumpreset":  #펌프 재시작
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET resetflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "roconfig":  #ro 값 변경, cal_ro_tb 테이블에는 데이터 존재
        for i in agrs[0]:
            sql = 'UPDATE sensoractiveconfig SET roflage = 1 WHERE sensorid = {0}'.format(i)
            curs.execute(sql)
            db.commit()
    if mode == "scopeconfig":  #scope 값 변경, cal_scope_tb 테이블에는 데이터 존재
        for i in agrs[0]:
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
            ro_send = 'idx{0},W,{1},A,{2:+07.3f},{3:+07.3f},{4:+07.3f},etx'.format(sensor_ids[sensor_id],items,float(ro_value[i]),float(sample_data),float(sample_data))
            app.logger.info(' Ro Send=%s', ro_send)
            # Save RO or Calibration VALUES calibrationtb(RO 혹은 scope 선택, 센서이름(MQ135~138), RO값 또는 Calibration값)
            save_RO_Calbration(items, float(ro_value[i]))
            ack_send = "0"
            #sendProcessFunction(sensor_ids[sensor_id], 'W', ro_send, ack_send)
            i += 1
    #모든 센서에 동작 시간 설정이 완료되면 재시작해야 설정된 값이 적용됨
    #config_reset(sensor_ids)
    
# 기울기값 변경 요청: idx1, W(대문자),5(6|7|8),0(1|2|3),X절편,Y절편,기울기,etx)-32자리
def config_scope_value(sensor_ids,scop0, scop1, scop2, scop3):
    scope_level_0= scop0.split(';') #135 센서의 모든것 
    scope_level_1= scop1.split(';') #136
    scope_level_2= scop2.split(';') #137
    scope_level_3= scop3.split(';') #138
    scope_list = scope_level_0,scope_level_1,scope_level_2,scope_level_3
    #app.logger.info(' Sensor count=%s, Sensor Len=%s, Scope_list=%s',sensor_ids, len(sensor_ids), scope_list)
    # Scope백업
    save_RO_Scope_Backup(2)
    for sensor_id in range(0, len(sensor_ids)): 
        for sensorname in range(0,4):
            for level in range(0,4):
                #app.logger.info('sensor name MQ13%s Value=%s Level=%s',sensorname+5, scope_list[sensorname], level)
                scop1 = scope_list[sensorname][level].split(',')
                #app.logger.info('scope_level 0 length all %s, 1 %s, 2 %s, 3 %s ',scope_list[level][0],scop1[0],scop1[1],scop1[2])
                scope_send = 'idx{0},W,{1},{2},{3:+07.3f},{4:+07.3f},{5:+07.3f},etx'.format(sensor_ids[sensor_id],sensorname+5,level,float(scop1[0]),float(scop1[1]),float(scop1[2]))
                save_Scope_Calbration(sensorname, level, float(scop1[0]), float(scop1[1]), float(scop1[2]))
                app.logger.info('scope send data %s',scope_send)
                ack_send = "0"
                #sendProcessFunction(sensor_ids[sensor_id], 'W', scope_send, ack_send)
    #모든 센서에 동작 시간 설정이 완료되면 재시작해야 설정된 값이 적용됨
    #config_reset(sensor_ids)
    
#RO 및 Scope 보정 작업하기 전에 백업 수행        
def save_RO_Scope_Backup(mode):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    nowtime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    try:
        if mode == 1:
            curs = db.cursor()
            backtbname = 'cal_ro_tb_{0}'.format(nowtime)
            sql = "CREATE TABLE  `{0}`  SELECT * FROM `cal_ro_tb`".format(backtbname)
            curs.execute(sql)
            db.commit()
        if mode == 2:
            curs = db.cursor()
            backtbname = 'cal_scope_tb_{0}'.format(nowtime)
            sql = "CREATE TABLE `{0}`  SELECT * FROM `cal_scope_tb`".format(backtbname)
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
        sql = "UPDATE cal_ro_tb SET RO_Value = {0}, checkdate = '{1}' WHERE SensorName='{2}'".format(value, nowtime, sensorname)
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
        sql = "UPDATE cal_scope_tb SET X_side = {0}, Y_side = {1}, Scope = {2}, checkdate = '{3}' WHERE SensorName='{4}' and level='{5}'".format(value1, value2, value3, nowtime, sensorname, level)
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
            curs.execute("INSERT INTO `sensorlog`  (`commands`, `InputDateTime`) VALUES (%s,%s)", (auto_send_cmd,nowtime))
        db.commit()
    finally:
        db.close()