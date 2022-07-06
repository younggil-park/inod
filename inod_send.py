#!/usr/bin/python
#-*- coding:utf-8 -*-
import sys
from datetime import datetime
import datetime
import serial
import time
import pymysql #MySQL 연결 위한 라이브러리
import random
import string
import secrets
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

serialPort1 = "/dev/ttyUSB0"
write_ser = serial.Serial(serialPort1, baudrate=19200, timeout = 1)
write_ser.flushInput()

ack_send = ""       

# run time 값 읽기 하나를 기준으로 처리함
def get_pump_run_time(sensor_id):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rundatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT intaketimes, fittimes, exhausttimes FROM sensorpumpruntime WHERE sensorid={0}".format(sensor_id)
            curs.execute(sql)
            rundatatb = list( curs.fetchall())
            msg = ' SensorID:{0}, time list:{1}'.format(sensor_id, rundatatb)
            logger.info('get_pump_run_time: %s',msg )
    finally:
        return rundatatb
        db.close()
        
# 센서 구동 시간은 구동시간 전송하고 바로 센서의 응답을 받아서 다음 구동시간을 전송해야하기때문에
# 센서의 응답확인을 체크하는 작업이 필요하다.
def runtime_response(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            # 센서 하나에서 cmdprocess에서 r_flag와 sensortickets에서 s_flag가 설정된것이 존재하는지 확인작업을 한다.
            sql = "SELECT * FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.r_flag=1 and B.s_flag=1 and A.cmd=B.cmd".format(sensorid)
            curs.execute(sql)
            rows = curs.rowcount
            if rows == 1:
                return False
            else:
                return True
    finally:
        db.close()
        
# 모든 작업 로그를 저장 한다.
def SaveLog(auto_send_cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    #logger.info('1-3.SaveLog %s',auto_send_cmd)
    try:
        with db.cursor() as curs:
            curs.execute("INSERT INTO `sensorlog`  (`commands`, `inputdatetime`) VALUES (%s,%s)", (auto_send_cmd,nowtime))
        db.commit()
    finally:
        db.close()

# 자동모드(흡기, 필팅, 배기) 동작 명령, 센서에서 데이터를 보내면 서버에서 응답을 해야 한다.
# idx1,),년,월,일,시,분,초,etx 
# # 카운터 모드(0)인지 무한 모드(1)
def send_request_data(sensor_ids, countmode, runcount=0):
    today = datetime.datetime.now()
    years = today.year
    months = today.month
    days = today.day
    hours = today.hour
    minutes = today.minute
    seconds = today.second
    
    auto_send_cmd = 'idx{0},),{1:02d},{2:02d},{3:02d},{4:02d},{5:02d},{6:02d},etx'.format(sensor_ids, years, months, days, hours,minutes, seconds)
    logger.info('1-1-2.autorun mode sensor No %s count %s cmd %s',sensor_ids, runcount, auto_send_cmd)
    ack_send = 'idx{0},1,etx'.format(sensor_ids)
    flag_name = 'runflage'
    sendProcessFunction(sensor_ids, 'bt', auto_send_cmd, ack_send, flag_name)
        
# SD카드에 있는 데이터 전송 요청 idx1,+,etx 
# 센서에서 데이터를 보내면 서버에서 응답을 해야 한다. 
# 이때 센서에서 응답코드가 2, 3을 보내면 데이터없음, 장애를 나타낸다.
def read_request_sdcard(sensor_ids):
    sd_send = 'idx{0},+,etx'.format(sensor_ids)
    #logger.info('sd send data %s',sd_send)
    ack_send = 'idx{0},1,etx'.format(sensor_ids)
    flag_name = 'sdreadflage'
    # 명령어 요청시 티켓을 생성하여 확인한다.
    sendProcessFunction(sensor_ids, 'ps', sd_send, ack_send, flag_name)

# 서버에서 배기 요청(idx1,,,etx)-10자리-check-ok
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def run_request_exhaust(sensor_ids):
    sd_send = 'idx{0},,,etx'.format(sensor_ids)
    #logger.info('export send data %s',export_send)
    ack_send = '0'
    flag_name = 'exhaustflage'
    sendProcessFunction(sensor_ids, 'ca', sd_send, ack_send, flag_name)

# 서버에서 흡기 요청(idx1,-,etx)-10자리 -check-ok
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def run_request_intake(sensor_ids):
    sd_send = 'idx{0},-,etx'.format(sensor_ids)
    #logger.info('import send data %s',import_send)
    ack_send = '0'
    flag_name = 'intakeflage'
    sendProcessFunction(sensor_ids, 'dh', sd_send, ack_send, flag_name)

# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
# Ro와 Scope, runningtimes을 수정하면 센서를 재시작해야 적용된다.
# 센서에서 별도의 응답은 없다.
def reset_request_sensor(sensor_ids):
    checktime = 0
    ro_send = 'idx{0},R,etx'.format(sensor_ids)
    ack_send = '0'
    flag_name = 'resetflage'
    sendProcessFunction(sensor_ids, 'R', ro_send, ack_send, flag_name)
    msg = ' Reset CMD SensorID:{0}, CMD:{1}'.format(sensor_ids, ro_send)
    logger.info('Command writting %s',msg )
    SaveLog(msg)
            
# 펌프 동작 시간 변경 요청: idx1, I|P|E (대문자),XXXXX,etx -16자리
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def runtime_setting_sensor(sensor_ids):
    checkflage = True
    # 5초면 전파의 속도(v) = 파장(λ) x 주파수(f)
    response_checktime = 5
    runningtimes = get_pump_run_time(sensor_ids)
    msg = ' SensorID:{0}, runningtimes:{1}'.format(sensor_ids, runningtimes)
    logger.info('runtime_setting_sensor %s',msg )
    
    intaketimes = '{0:05d}'.format(runningtimes[0][0])
    fittimes = '{0:05d}'.format(runningtimes[0][1])
    exhausttimes = '{0:05d}'.format(runningtimes[0][2])
    
    check_count = 0
    intaketimes_set = 'idx{0},I,{1},etx'.format(sensor_ids, intaketimes)
    fittimes_set = 'idx{0},P,{1},etx'.format(sensor_ids, fittimes)
    exhausttimes_set = 'idx{0},E,{1},etx'.format(sensor_ids, exhausttimes)
    
    #흡기 시간 설정 전송
    ack_send = '0'
    flag_name = 'runtimeflage'
    sendProcessFunction(sensor_ids, 'I', intaketimes_set, ack_send, flag_name)
    while checkflage:
        checkflage = runtime_response(sensor_ids)
        if check_count < response_checktime:
            time.sleep(1)
            check_count += 1
        else:
            break
    time.sleep(5)
    
    #양생 시간 설정 전송
    ack_send = '0'
    flag_name = 'runtimeflage'
    sendProcessFunction(sensor_ids, 'P', fittimes_set, ack_send, flag_name)
    while checkflage:
        checkflage = runtime_response(sensor_ids)
        if check_count < response_checktime:
            time.sleep(1)
            check_count += 1
        else:
            break
    time.sleep(5)
    
    #배기 시간 설정 전송
    ack_send = '0'
    flag_name = 'runtimeflage'
    sendProcessFunction(sensor_ids, 'E', exhausttimes_set, ack_send, flag_name)
    while checkflage:
        checkflage = runtime_response(sensor_ids)
        if check_count < response_checktime:
            time.sleep(1)
            check_count += 1
        else:
            break
    time.sleep(5)
    
# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def ro_setting_sensor(sensor_ids):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rodatatb = []
    rodatatb2 = []
    try:
        with db.cursor() as curs:
            sql = "select sensorname, ro_value from calrovalue"
            curs.execute(sql)
            rows = curs.rowcount
            logger.info("rows counters: %s",rows )
            #한번 호출할때 전체 row 레코드 갖고오므로 1차 리스로 바꾸고
            rodata = list(curs.fetchall())
            # 2차 list 로 변환
            for x in range(0, rows):
                rodatatb2.append(list(rodata[x]))
            msg = "tuple to list:{0}".format(rodatatb2)
            logger.info('get_rotb4 %s',msg )
    finally:
        db.close()

    sample_data = +00.000
    for i in range(0, len(rodatatb2)):
        ro_send = ""
        if rodatatb2[i][0] == "MQ135": sensorname = 5
        if rodatatb2[i][0] == "MQ136": sensorname = 6
        if rodatatb2[i][0] == "MQ137": sensorname = 7
        if rodatatb2[i][0] == "MQ138": sensorname = 8
        ro_send = "idx{0},W,{1},A,{2:+07.3f},{3:+07.3f},{4:+07.3f},etx".format(sensor_ids,sensorname,float(rodatatb2[i][1]),float(sample_data),float(sample_data))
        logger.info("ro_send data: %s", ro_send )
        ack_send = '0'
        flag_name = 'roflage'
        sendProcessFunction(sensor_ids, 'W', ro_send, ack_send, flag_name)
        time.sleep(2)
                            
def scope_setting_sensor(sensor_ids):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rodatatb = []
    rodatatb2 = []
    try:
        with db.cursor() as curs:
            sql = "SELECT sensorname, level, x_side, y_side, scope FROM calscopevalue"
            curs.execute(sql)
            rows = curs.rowcount
            logger.info("rows counters: %s",rows )
            #한번 호출할때 전체 row 레코드 갖고오므로 1차 리스로 바꾸고
            rodata = list(curs.fetchall())
            # 2차 list 로 변환
            for x in range(0, rows):
                rodatatb2.append(list(rodata[x]))
            msg = "tuple to list:{0}".format(rodatatb2)
            logger.info('get_rotb4 %s',msg )
    finally:
        db.close()

    for i in range(0, len(rodatatb2)):
        scope_send = ""
        if rodatatb2[i][0] == "MQ135": sensorname = 5
        if rodatatb2[i][0] == "MQ136": sensorname = 6
        if rodatatb2[i][0] == "MQ137": sensorname = 7
        if rodatatb2[i][0] == "MQ138": sensorname = 8
        scope_send = 'idx{0},W,{1},{2},{3:+07.3f},{4:+07.3f},{5:+07.3f},etx'.format(sensor_ids,sensorname,rodatatb2[i][1],float(rodatatb2[i][2]),float(rodatatb2[i][3]),float(rodatatb2[i][4]))  
        logger.info("scope_send data: %s", scope_send )
        ack_send = '0'
        flag_name = 'scopeflage'
        sendProcessFunction(sensor_ids, 'W', scope_send, ack_send, flag_name)
        time.sleep(2)

# 유일한 티켓을 생성하는 부분
def new_ticket_generator():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "select uuid_short()"
            curs.execute(str_query)
            tickets = list(curs.fetchone())
            msg = ' tickets={1}'.format(tickets)
            logger.info('tickets  %s',msg )
    finally:
        return tickets
        db.close()
        
# send_data, modes=auto(자동), sdcard(카드)
# 서버에서 요청하면 센서에서 데이터 주고, 서버는 받았다는 결과를 전송
# 자동모드 
# S: idx0,) ,년,월,일,시,분,etx -> C: idx0, 10자리 ~ ,etx -> S: idx0,1,etx
# 카드 읽기
# S: idx0,+,etx -> C: idx0, 10자리 ~ ,etx -> S: idx0,1,etx -> C: idx0, 10자리 ~ ,etx ->
# 데이터 없으면 C:idx0,2,etx  / 카드에러 C:idx0,3,etx
 
def sendProcessFunction(sensor_id, cmd, send_data, ack_send, flage_check):
    #명령 처리 티켓 생성
    new_tickets = new_ticket_generator()
    # 티켓을 생성하면서 보냈다는 프래그를 1로 설정한다.
    create_cmdprocess_and_ticket(sensor_id, cmd, new_tickets[0], ack_send)
    # 서버에서 명령어 전송(자동 모드와 SD 카드 읽기 명령)
    write_ser.write(send_data.encode("utf-8"))
    #동작 시간 설정의 경우는 결과 값이 없이 그냥 설정을 하고 리셋만을 하기때문에
    # 티켓 결과 처리와 명령 결과 처리를 바로 해줘야 한다.
    if cmd == "I" or cmd == "P" or cmd == "E" or cmd == "R":
        pump_set_result_update(sensor_id, cmd, new_tickets[0])
        
    # sensoractiveconfig의 프래그를 2로 변경하는 작업을 한다.
    sensoractiveconfig_flag_update(sensor_id, flage_check)
    logger.info('sendProcessFunction cmd writting %s',send_data )
    SaveLog(send_data)

# 펌브 동작 시간과 리셋의 경우에는 프래그를 완료로 처리한다.
def pump_set_result_update(sensor_id, cmd, tickets):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    curs = db.cursor()
    sql = "UPDATE sensortickets A, cmdprocess B SET B.r_flag = 1, B.f_flag = 1, B.r_time = '{0}', B.f_time = '{0}', A.s_flag = 3 WHERE A.sensorid = {1} and B.sensorid={1} and A.tickets = '{2}' and B.tickets = '{2}' and B.r_flag = 0 and B.f_flag = 0 ".format(nowtime, sensor_id, tickets)
    curs.execute(sql)
    db.commit()
    if cmd == "R":
        sql = "UPDATE sensoractiveconfig SET runflage=0, runcount=0, sdreadflage=0,exhaustflage=0,intakeflage=0,resetflage=0,runtimeflage=0,roflage=0,scopeflage=0,countmode=0,runtimecheck=0 WHERE sensorid = {0}".format(sensor_id)
        curs.execute(sql)
        db.commit()
    db.close()
    
# 서버에서 처음 송신을 하고 S_Flage를 1로 설정한다.
# 센서에서 보낸 수신 정보를 확인해서 요청 명령임을 확인하면 R_Flage를 1 로 설정한다.
# 서버에서 R_Flage 를 확인하여 응답 정보를 보내고 F_Flage 를 1로 설정하면 명령 처리가 모두 끝난것으로 판단한다.
# =>완료 후 sensortickets 테이블의 S_Flage를 (서버 명령전송 1, 센서 응답 2, 서버에서 ack_send 또는 ack_send 없으면 3)로 설정
# 명령 처리 완료 유무와 티켓 생성을 처리한다. *args = cmd, new_tickets, ack_send
def create_cmdprocess_and_ticket(sensor_id, *args):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "INSERT INTO  sensortickets  (sensorid, cmd, tickets, ack_send, s_flag, s_time) VALUES({0}, '{1}', '{2}', '{3}', 1, '{4}')".format(sensor_id, args[0], args[1], args[2], nowtime)
            curs.execute(str_query)
        db.commit()
        with db.cursor() as curs:
            str_query = "INSERT INTO  cmdprocess  (sensorid, cmd, tickets, s_flag, r_flag, f_flag, s_time) VALUES({0}, '{1}', '{2}', 1, 0, 0, '{3}')".format(sensor_id, args[0], args[1], nowtime)
            curs.execute(str_query)
        db.commit()
        
    finally:
        db.close()

# 전송 처리되었다는 의미로 프래그를 2로 설정한다.
#mode = autorun, sd_read, exhaust, intake, pumpruntime, pumpreset, roconfig, scopeconfig
def sensoractiveconfig_flag_update(sensorids, mode):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    curs = db.cursor()
    
    if mode == "runtimeflage":  #펌프 동작 시간 설정
        sql = 'UPDATE sensoractiveconfig A, sensorpumpruntime B SET A.{0} = 2, B.checkflage = 2 WHERE A.sensorid = {1} and B.sensorid={1}'.format(mode, sensorids)
    else:
        sql = 'UPDATE sensoractiveconfig SET {0} = 2 WHERE sensorid = {1}'.format(mode, sensorids)
    curs.execute(sql)
    db.commit()
    db.close()
    
# flage값이 1이면 동작, 0 완료
#무한 반복 펌프 동작 유무 runflage = 1
#SD카드에서 데이터 읽기 sdreadflage = 1
#배기 펌프 동작 exhaustflage = 1
#흡기 펌프 동작 intakeflage = 1
#펌프 재시작 resetflage = 1
#펌프 동작 시간 설정 runtimeflage = 1
#ro 값 변경 roflage = 1
#scope 값 변경 scopeflage = 1
# sensorid부터 해서 총 9개의 자료를 받는다.
def db_check():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    curs = db.cursor()
    sql = 'SELECT  sensorid, runflage, sdreadflage, exhaustflage, intakeflage, resetflage, runtimeflage, roflage, scopeflage, runcount, countmode FROM sensoractiveconfig WHERE runflage = 1 or sdreadflage = 1 or exhaustflage = 1 or intakeflage = 1 or resetflage = 1 or runtimeflage = 1 or roflage = 1 or scopeflage = 1'
    curs.execute(sql)
    rows = curs.rowcount
    
    # 명령을 요청한 정보 테이블에서 센서들의 정보를 확인한다.
    if rows == 0:
        request_flag = 0
        return rows, request_flag
    else:
        request_flag = curs.fetchall()
        #request_flag = [item['cmd'] for item in curs.fetchall()]
        msg = "There are {1} data to be sent to {0} sensors.".format(rows, request_flag)
        logger.info('main loop.db_check message: %s',msg )
        return rows, request_flag
    db.close()
        
#중지 명령이거나 카운터 값이 모두 처리된경우 자동모드를 종료하여야 한다.
def clear_runflage(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = 'UPDATE sensoractiveconfig SET runflage=0, runcount=0, sdreadflage=0,exhaustflage=0,intakeflage=0,resetflage=0,runtimeflage=0,roflage=0,scopeflage=0,countmode=0,runtimecheck=0 WHERE sensorid = {0}'.format(sensorid)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
                            
if __name__ == "__main__":
    #main 프로그램 시작
    logger.info('This program is an inod_send program that sends data.' )
    logger.info('Check if there is data to send, and if there is data, send it.' )
    check_flag = False
    while True:
        try:
            # sensorid부터 해서 총 10개의 자료를 받는다.
            rows, datas = db_check()
            if rows == 0: continue
            msg = "rows counter={0} Data:={1}".format(rows, datas)
            logger.info('setting : %s',msg )
            # 센서들을 선택
            for i in range(0,rows):
                # 해당 센서의 명령 프래그 선택
                msg = "rows counter={0} ".format(i)
                logger.info('setting : %s',msg )
                list_data = [list(datas[x]) for x in range(len(datas))]
                msg = "rows ={1}, data={0} ".format(list_data[i],i)
                logger.info('setting : %s',msg )
                
                sensorid = list_data[i][0]
                runflage = list_data[i][1]
                sdreadflage = list_data[i][2]
                exhaustflage = list_data[i][3]
                intakeflage = list_data[i][4]
                resetflage = list_data[i][5]
                runtimeflage = list_data[i][6]
                roflage = list_data[i][7]
                scopeflage = list_data[i][8]
                runcount = list_data[i][9]
                countmode = list_data[i][10]

                if runflage == 1 and countmode == 0: #카운터 값이 존재하는 유한 자동모드
                    send_request_data(sensorid, countmode, runcount)
                    check_flag = True
                    msg = "rows={4} Data: sensorid={0}, runflage={1}, runcount={2}, countmode={3}.".format(sensorid,runflage,runcount,countmode,i)
                    logger.info('setting : %s',msg )
                elif runflage == 1 and countmode == 1:  #카운터 값이 없는 즉 무한 자동모드
                    send_request_data(sensorid, countmode)
                    check_flag = True
                    msg = "rows={4} Data: sensorid={0}, runflage={1}, runcount={2}, countmode={3}.".format(sensorid,runflage,runcount,countmode,i)
                    logger.info('setting : %s',msg )
                elif sdreadflage == 1: 
                    read_request_sdcard(sensorid)
                    check_flag = True
                    msg = "rows={2} Data: sensorid={0}, sdreadflage={1}".format(sensorid,sdreadflage,i)
                    logger.info('setting : %s',msg )
                elif exhaustflage == 1: 
                    run_request_exhaust(sensorid)
                    msg = "rows={2} Data: sensorid={0}, exhaustflage={1}".format(sensorid,exhaustflage,i)
                    logger.info('setting : %s',msg )
                elif intakeflage == 1: 
                    run_request_intake(sensorid)
                    msg = "rows={2} Data: sensorid={0}, intakeflage={1}.".format(sensorid,intakeflage,i)
                    logger.info('setting : %s',msg )
                elif resetflage == 1: 
                    reset_request_sensor(sensorid) #수동으로 리셋을 하는 경우
                    msg = "rows={2} Data: sensorid={0}, resetflage={1}.".format(sensorid,resetflage,i)
                    logger.info('setting : %s',msg )
                elif runtimeflage == 1:
                    runtime_setting_sensor(sensorid)
                    reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    msg = "rows={2} Data: sensorid={0}, runtimeflage={1}.".format(sensorid,runtimeflage,i)
                    logger.info('setting : %s',msg )
                elif roflage == 1:
                    ro_setting_sensor(sensorid)
                    reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    msg = "rows={2} Data: sensorid={0}, roflage={1}.".format(sensorid,roflage,i)
                    logger.info('setting : %s',msg )
                elif scopeflage == 1:
                    scope_setting_sensor(sensorid)
                    reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    msg = "rows={2} Data: sensorid={0}, scopeflage={1}.".format(sensorid,scopeflage,i)
                    logger.info('setting : %s',msg )
                time.sleep(2)
        except KeyboardInterrupt:
            sys.exit()
        time.sleep(5)
    
