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

serialPort1 = "/dev/ttyUSB0"
write_ser = serial.Serial(serialPort1, baudrate=19200, timeout = 1)
write_ser.flushInput()

ack_send = ""

# 유일한 티켓을 생성하는 부분
def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def new_ticket_generator(instance):
    new_tickets= random_string_generator()
    
    qs_exists= check_ticket(new_tickets)
    if qs_exists >= 1:
        return new_ticket_generator(instance)
    return new_tickets
    
# 기존에 발행한 티켓 존재하는지를 확인한다.
# 유일한 티켓을 발행하기 위하여
def check_ticket(tickets):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "SELECT tickets  FROM sensortickets  WHERE TICKETS={0} AND S_FLAG=0".format(tickets)
            curs.execute(str_query)
            flags = curs.rowcount
    finally:
        db.close()
        return flags
        
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

# run time 값 읽기 하나를 기준으로 처리함
def get_pump_run_time(sensor_id):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rundatatb = []
    try:
        with db.cursor() as curs:
            #sql = "SELECT intaketimes, fittimes, exhausttimes FROM sensorpumpruntime where sensorid = {}".format(sensor_id)
            sql = "SELECT intaketimes, fittimes, exhausttimes FROM sensorpumpruntime"
            curs.execute(sql)
            rundatatb = curs.fetchall()
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
            sql = "SELECT * FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.r_flag=1 and B.s_flag=2 and A.cmd=B.cmd".format(sensorid)
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
    #app.logger.info('1-3.SaveLog %s',auto_send_cmd)
    try:
        with db.cursor() as curs:
            curs.execute("INSERT INTO `sensorlog`  (`commands`, `InputDateTime`) VALUES (%s,%s)", (auto_send_cmd,nowtime))
        db.commit()
    finally:
        db.close()

# 자동모드(흡기, 필팅, 배기) 동작 명령, 센서에서 데이터를 보내면 서버에서 응답을 해야 한다.
# idx1,),년,월,일,시,분,초,etx 
# # 카운터 모드(0)인지 무한 모드(1)
def send_request_data(sensorid, countmode, runcount=0):
    today = datetime.datetime.now()
    years = today.year
    months = today.month
    days = today.day
    hours = today.hour
    minutes = today.minute
    seconds = today.second
    
    auto_send_cmd = 'idx{0},),{1:02d},{2:02d},{3:02d},{4:02d},{5:02d},{6:02d},etx'.format(sensor_ids[sensor_id], years, months, days, hours,minutes, seconds)
    app.logger.info('1-1-2.autorun mode sensor No %s count %s cmd %s',sensor_ids, countcheck, auto_send_cmd)
    ack_send = 'idx{0},1,etx'.format(sensor_ids)
    
    # 카운터 모드(0)이면 카운터 값을 하나씩 뺀다.
    if countmode == 0:
        if runcount > 0:
            degree_count(sensorid)
            # 명령어 요청시 티켓을 생성하여 확인한다.
            sendProcessFunction(sensor_ids, ')', auto_send_cmd, ack_send)
        else:
            # 카운터 값이 0이 되면 초기화한다.
            clear_runflage(sensorid)
    else: # 자동 모드 (1)이면 데이터 전송
        # 명령어 요청시 티켓을 생성하여 확인한다.
        sendProcessFunction(sensor_ids, ')', auto_send_cmd, ack_send)

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
        
# SD카드에 있는 데이터 전송 요청 idx1,+,etx 
# 센서에서 데이터를 보내면 서버에서 응답을 해야 한다. 
# 이때 센서에서 응답코드가 2, 3을 보내면 데이터없음, 장애를 나타낸다.
def read_request_sdcard(sensor_ids):
    sd_send = 'idx{0},+,etx'.format(sensor_id)
    #app.logger.info('sd send data %s',sd_send)
    ack_send = 'idx{0},1,etx'.format(sensor_id)
    # 명령어 요청시 티켓을 생성하여 확인한다.
    sendProcessFunction(sensor_id, '+', sd_send, ack_send)

# 서버에서 배기 요청(idx1,,,etx)-10자리
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def run_request_exhaust(sensor_ids):
    sd_send = 'idx{0},,,etx'.format(sensor_ids)
    #app.logger.info('export send data %s',export_send)
    ack_send = '0'
    sendProcessFunction(sensor_id, ',', sd_send, ack_send)

# 서버에서 흡기 요청(idx1,-,etx)-10자리
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def run_request_intake(sensor_ids):
    sd_send = '0'
    #app.logger.info('import send data %s',import_send)
    ack_send = 'idx{0},2,etx'.format(sensor_ids)
    sendProcessFunction(sensor_id, '-', sd_send, ack_send)

# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
# Ro와 Scope, runningtimes을 수정하면 센서를 재시작해야 적용된다.
# 센서에서 별도의 응답은 없다.
def reset_request_sensor(sensor_ids):
    checktime = 0
    ro_send = 'idx{0},R,etx'.format(sensor_ids[sensor_id])
    ack_send = '0'
    sendProcessFunction(sensor_ids, 'R', ro_send, ack_send)
    msg = ' Reset CMD SensorID:{0}, CMD:{1}'.format(sensor_ids, ro_send)
    app.logger.info('Command writting %s',msg )
    SaveLog(msg)
            
# 펌프 동작 시간 변경 요청: idx1, I|P|E (대문자),XXXXX,etx -16자리
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def runtime_setting_sensor(sensor_ids):
    checkflage = True
    # 5초면 전파의 속도(v) = 파장(λ) x 주파수(f)
    response_checktime = 5
    runningtimes = get_pump_run_time(sensor_ids)
    intaketimes = '{0:05d}'.format(runningtimes[0][0])
    fittimes = '{0:05d}'.format(runningtimes[0][1])
    exhausttimes = '{0:05d}'.format(runningtimes[0][2])
    
    check_count = 0
    intaketimes_set = 'idx{0},I,{1},etx'.format(sensor_ids, intaketimes)
    fittimes_set = 'idx{0},P,{1},etx'.format(sensor_ids, fittimes)
    exhausttimes_set = 'idx{0},E,{1},etx'.format(sensor_ids, exhausttimes)
    
    #흡기 시간 설정 전송
    ack_send = '0'
    sendProcessFunction(sensor_ids, 'I', intaketimes_set, ack_send)
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
    sendProcessFunction(sensor_ids, 'P', fittimes_set, ack_send)
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
    sendProcessFunction(sensor_ids, 'E', exhausttimes_set, ack_send)
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
    rowscope = get_rotb()
    sample_data = +00.000
    i = 0
    for rows in rowsscope:
        ro_send = ""
        if rows[i][0] == "MQ135": sensorname = 5
        if rows[i][0] == "MQ136": sensorname = 6
        if rows[i][0] == "MQ137": sensorname = 7
        if rows[i][0] == "MQ138": sensorname = 8
        ro_send = 'idx{0},W,{1},A,{2:+07.3f},{3:+07.3f},{4:+07.3f},etx'.format(sensor_ids,sensorname,float(rows[i][1]),float(sample_data),float(sample_data))

        ack_send = '0'
        sendProcessFunction(sensor_ids, 'W', ro_send, ack_send)
        time.sleep(1)
        i += i
    
# 기울기값 변경 요청: idx1, W(대문자),5(6|7|8),0(1|2|3),X절편,Y절편,기울기,etx)-32자리
# 센서에서 데이터를 보내면 서버에서 별도의 응답 없다.
def scope_setting_sensor(sensor_ids):
    rowscope = get_scopetb()
    i = 0
    for rows in rowsscope:
        scope_send = ""
        if rows[i][0] == "MQ135": sensorname = 5
        if rows[i][0] == "MQ136": sensorname = 6
        if rows[i][0] == "MQ137": sensorname = 7
        if rows[i][0] == "MQ138": sensorname = 8
        scope_send = 'idx{0},W,{1},{2},{3:+07.3f},{4:+07.3f},{5:+07.3f},etx'.format(sensor_ids,sensorname,rows[i][1],float(rows[i][2]),float(rows[i][3]),float(rows[i][4]))       
        ack_send = '0'
        sendProcessFunction(sensor_ids, 'W', scope_send, ack_send)
        time.sleep(1)
        i += 1
    
# send_data, modes=auto(자동), sdcard(카드)
# 서버에서 요청하면 센서에서 데이터 주고, 서버는 받았다는 결과를 전송
# 자동모드 
# S: idx0,) ,년,월,일,시,분,etx -> C: idx0, 10자리 ~ ,etx -> S: idx0,1,etx
# 카드 읽기
# S: idx0,+,etx -> C: idx0, 10자리 ~ ,etx -> S: idx0,1,etx -> C: idx0, 10자리 ~ ,etx ->
# 데이터 없으면 C:idx0,2,etx  / 카드에러 C:idx0,3,etx
 
def sendProcessFunction(sensor_id, cmd, send_data, ack_send):
    #명령 처리 티켓 생성
    new_tickets = new_ticket_generator()
    # 티켓을 생성하면서 보냈다는 프래그를 1로 설정한다.
    create_cmdprocess_and_ticket(sensor_id, cmd, new_tickets, ack_send)
    # 서버에서 명령어 전송(자동 모드와 SD 카드 읽기 명령)
    write_ser.write(send_data.encode("utf-8"))
    app.logger.info('1-2.Command writting %s',send_data )
    SaveLog(send_data)

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
            str_query = "INSERT INTO  sensortickets  (SENSORID, CMD, TICKETS, ACK_SEND, S_FLAG, S_TIME) VALUES({0},{1},{2},{3})".format(sensorid, args[0], args[1], args[2], 1, nowtime)
            curs.execute(str_query)
        db.commit()
        with db.cursor() as curs:
            str_query = "INSERT INTO  cmdprocess  (SENSORID, CMD, TICKETS, S_FLAG, S_TIME) VALUES({0},{1},{2},{3})".format(sensorid, args[0], args[1], 1, nowtime)
            curs.execute(str_query)
        db.commit()
    finally:
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
        msg = "There are {1} data to be sent to {0} sensors.".format(rows, request_flag)
        app.logger.info('main loop.db_check message: %s',msg )
        return rows, request_flag
    db.close()

def tick_result_check(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    results = "0"
    rows = 0
    try:
        with db.cursor() as curs:
			sql = "SELECT A.ack_send FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.s_flag=1 and A.r_flag=1 and B.s_flag=2 and A.cmd=B.cmd and A.f_flag=0".format(sensorid)
            curs.execute(sql)
            rows = curs.rowcount
            if rows > 0:
                results = curs.fetchall()
    finally:
        return results
        db.close()
        
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

# 자동모드와 카드 읽기 모드의 경우 해당 센서에 응답을 보내야 하는 값이 있으면
# 처리하도록 한다. read에서 SD 카드에 대한 2,3 값을 받으면 ack_send를 0으로 처리하기때문에
# 0이 아니면 명령을 보낸다.
def auto_sdcard_mode(sensorid):
    # 처리 결과를 확인해서 응답이 있는 부분은 응답을 보낸다. ) 와 +
    results = tick_result_check(sensorid)
    if results != "0":
        write_ser.write(results.encode("utf-8"))
        app.logger.info('Command writting %s',results )
        SaveLog(results)
                            
if __name__ == "__main__":
    #main 프로그램 시작
    app.logger.info('This program is an inod_send program that sends data.' )
    app.logger.info('Check if there is data to send, and if there is data, send it.' )
    while True:
        check_flag = False
        try:
            # sensorid부터 해서 총 9개의 자료를 받는다.
            rows, datas = db_check()
            if rows == 0: continue
            
            # 센서들을 선택
            for i in range(0,rows):
                # 해당 센서의 명령 프래그 선택
                for actions in datas:
                    sensorid = actions[i][0]
                    runflage = actions[i][1]
                    sdreadflage = actions[i][2]
                    exhaustflage = actions[i][3]
                    intakeflage = actions[i][4]
                    resetflage = actions[i][5]
                    runtimeflage = actions[i][6]
                    roflage = actions[i][7]
                    scopeflage = actions[i][8]
                    runcount = actions[i][9]
                    countmode = actions[i][10]

                    if runflage == 1 and countmode = 0: #카운터 값이 존재하는 자동모드
                        send_request_data(sensorid, countmode, runcount)
                        check_flag = True
                    elif runflage == 1 and countmode = 1:  #카운터 값이 없는 즉 무한 자동모드
                        send_request_data(sensorid, countmode)
                        check_flag = True
                    elif sdreadflage == 1: 
                        read_request_sdcard(sensorid)
                        check_flag = True
                    elif exhaustflage == 1: run_request_exhaust(sensorid)
                    elif intakeflage == 1: run_request_intake(sensorid)
                    elif resetflage == 1: reset_request_sensor(sensorid) #수동으로 리셋을 하는 경우
                    elif runtimeflage == 1:
                        runtime_setting_sensor(sensorid)
                        reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    elif roflage == 1:
                        ro_setting_sensor(sensorid)
                        reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    elif scopeflage == 1:
                        scope_setting_sensor(sensorid)
                        reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    
                    # 자동 모드와 sd카드 모드에 대해서는 응답을 처리해야 하는것이 있어서 검사한다.
                    if check_flag:
                        auto_sdcard_mode(sensorid)
                    time.sleep(2)
        except KeyboardInterrupt:
            sys.exit()
        time.sleep(5)
    
