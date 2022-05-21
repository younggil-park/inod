from datetime import datetime
import datetime
import serial
from app001 import routes_all
from app001 import app
import time
import pymysql #MySQL 연결 위한 라이브러리

serialPort1 = "/dev/ttyUSB0"
write_ser = serial.Serial(serialPort1, baudrate=19200, timeout = 1)
write_ser.flushInput()

ack_send = ""

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

# 유일한 티켓을 생성하는 부분
import random
import string

def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def new_ticket_generator(instance):
    new_tickets= random_string_generator()
    
    qs_exists= check_ticket(new_tickets)
    if qs_exists >= 1:
        return new_ticket_generator(instance)
    return new_tickets

def check_ticket(tickets):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "SELECT tickets  FROM sensortickets  WHERE TICKETS={0} AND S_FLAGE=0".format(tickets)
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

# run time 값 읽기
def get_pump_run_time(sensor_id):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rundatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT intaketimes, fittimes, exhausttimes FROM sensorpumpruntime where sensorid = {}".format(sensor_id)
            curs.execute(sql)
            rundatatb = curs.fetchall()
    finally:
        return rundatatb
        db.close()

def runtime_response(sensorid):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "SELECT * FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.s_flag=1 and B.s_flag=1".format(sensorid)
            curs.execute(sql)
            rows = curs.rowcount()
            if rows == 1:
                return False
            else:
                return True
    finally:
        db.close()
        
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

# 자동모드 동작 명령        
def send_request_data(sensorid):
    today = datetime.datetime.now()
    years = today.year
    months = today.month
    days = today.day
    hours = today.hour
    minutes = today.minute
    seconds = today.second
    
    auto_send_cmd = 'idx{0},),{1:02d},{2:02d},{3:02d},{4:02d},{5:02d},{6:02d},etx'.format(sensor_ids[sensor_id], years, months, days, hours,minutes, seconds)
    app.logger.info('1-1-2.autorun sensor No %s count %s cmd %s',sensor_ids, countcheck, auto_send_cmd)
    ack_send = 'idx{0},1,etx'.format(sensor_ids)
    
    # 명령어 요청시 티켓을 생성하여 확인한다.
    sendProcessFunction(sensor_ids, ')', auto_send_cmd, ack_send)
    
# SD카드에 있는 데이터 전송 요청 idx1,+,etx 
def read_request_sdcard(sensor_ids):
    sd_send = 'idx{0},+,etx'.format(sensor_id)
    #app.logger.info('sd send data %s',sd_send)
    ack_send = 'idx{0},1,etx'.format(sensor_id)
    # 명령어 요청시 티켓을 생성하여 확인한다.
    sendProcessFunction(sensor_id, '+', sd_send, ack_send)

# 서버에서 배기 요청(idx1,,,etx)-10자리
def run_request_exhaust(sensor_ids):
    sd_send = 'idx{0},,,etx'.format(sensor_ids)
    #app.logger.info('export send data %s',export_send)
    ack_send = "0"
    sendProcessFunction(sensor_id, ',', sd_send, ack_send)

# 서버에서 흡기 요청(idx1,-,etx)-10자리
def run_request_intake(sensor_ids):
    sd_send = 'idx{0},-,etx'.format(sensor_ids)
    #app.logger.info('import send data %s',import_send)
    ack_send = "0"
    sendProcessFunction(sensor_id, '-', sd_send, ack_send)

# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
def reset_request_sensor(sensor_ids):
    checktime = 0
    ro_send = 'idx{0},R,etx'.format(sensor_ids[sensor_id])
    ack_send = "0"
    sendProcessFunction(sensor_ids, 'R', ro_send, ack_send)
    msg = ' Reset CMD SensorID:{0}, CMD:{1}'.format(sensor_ids, ro_send)
    app.logger.info('Command writting %s',msg )
    SaveLog(msg)
            
# 펌프 동작 시간 변경 요청: idx1, I|P|E (대문자),XXXXX,etx -16자리
def runtime_setting_sensor(sensor_ids):
    checkflage = True
    #intaketimes, fittimes, exhausttimes
    runningtimes = get_pump_run_time(sensor_ids)
    intaketimes = '{0:05d}'.format(runningtimes[0])
    fittimes = '{0:05d}'.format(runningtimes[1])
    exhausttimes = '{0:05d}'.format(runningtimes[2])
    
    ack_send = "0"
    check_count = 0
    intaketimes_set = 'idx{0},I,{1},etx'.format(sensor_ids, intaketimes)
    fittimes_set = 'idx{0},P,{1},etx'.format(sensor_ids, fittimes)
    exhausttimes_set = 'idx{0},E,{1},etx'.format(sensor_ids, exhausttimes)
    
    #흡기 시간 설정 전송
    sendProcessFunction(sensor_ids, 'I', intaketimes_set, ack_send)
    while checkflage:
        checkflage = runtime_response(sensor_ids)
        if check_count < 3:
            time.sleep(1)
            check_count += 1
        else:
            break
    time.sleep(5)
    
    #양생 시간 설정 전송
    sendProcessFunction(sensor_ids, 'P', fittimes_set, ack_send)
    while checkflage:
        checkflage = runtime_response(sensor_ids)
        if check_count < 3:
            time.sleep(1)
            check_count += 1
        else:
            break
    time.sleep(5)
    
    #배기 시간 설정 전송
    sendProcessFunction(sensor_ids, 'E', exhausttimes_set, ack_send)
    while checkflage:
        checkflage = runtime_response(sensor_ids)
        if check_count < 3:
            time.sleep(1)
            check_count += 1
        else:
            break
    time.sleep(5)
    
    
# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
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

        ack_send = "0"
        sendProcessFunction(sensor_ids, 'W', ro_send, ack_send)
        time.sleep(1)
        i += i
    
# 기울기값 변경 요청: idx1, W(대문자),5(6|7|8),0(1|2|3),X절편,Y절편,기울기,etx)-32자리
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
        ack_send = "0"
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
    create_cmdprocess_and_ticket(sensor_id, cmd, new_tickets, ack_send)
    # 서버에서 명령어 전송(자동 모드와 SD 카드 읽기 명령)
    write_ser.write(send_data.encode("utf-8"))
    app.logger.info('1-2.Command writting %s',send_data )
    SaveLog(send_data)

'''
CREATE TABLE `sensortickets` (
  `num` int(11) NOT NULL,
  `sensorid` varchar(1) NOT NULL,
  `cmd` varchar(2) NOT NULL,
  `ack_send` varchar(15) NOT NULL,
  `tickets` varchar(10) NOT NULL,
  `s_flag` varchar(1) NOT NULL,
  `s_time` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `cmdprocess` (
  `num` int(11) NOT NULL,
  `sensorid` varchar(1) NOT NULL,
  `cmd` varchar(2) NOT NULL,
  `tickets` varchar(10) NOT NULL,
  `s_flag` varchar(1) NOT NULL,
  `r_flag` varchar(1) DEFAULT NULL,
  `f_flag` varchar(1) DEFAULT NULL,
  `s_time` datetime NOT NULL,
  `r_time` datetime DEFAULT NULL,
  `f_time` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
'''
# 송신 서버에서 처음 송신을 하고 S_Flage를 1로 설정한다.
# 수신 서버에서 수신 정보를 확인해서 요청 명령임을 확인하면 R_Flage를 1 로 설정한다.
# 송신 서버에서 R_Flage 를 확인하여 응답 정보를 보내고 F_Flage 를 1로 설정하면 명령 처리가 모두 끝난것으로 판단한다.
#       =>완료 후 sensortickets 테이블의 S_Flage를 1로 설정하여 명령 처리 종료를 하여야 한다.
# 명령처리 완료 유무와 티켓 생성을 처리한다. *args = cmd, new_tickets, ack_send
def create_cmdprocess_and_ticket(sensor_id, *args):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "INSERT INTO  sensortickets  (SENSORID, CMD, TICKETS, ACK_SEND, S_FLAGE, S_TIME) VALUES({0},{1},{2},{3})".format(sensorid, args[0], args[1], args[2], 0, nowtime)
            curs.execute(str_query)
        db.commit()
        with db.cursor() as curs:
            str_query = "INSERT INTO  cmdprocess  (SENSORID, CMD, TICKETS, S_FLAGE, S_TIME) VALUES({0},{1},{2},{3})".format(sensorid, args[0], args[1], 0, nowtime)
            curs.execute(str_query)
        db.commit()
    finally:
        db.close()


#명령 결과 확인 
def SearchcmdProcess(sensorid, cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "SELECT r_flag FROM  cmdprocess  WHERE sensorid={0} AND CMD={1} AND S_FLAG={2}".format(sensorid, cmd, 0)
            curs.execute(str_query)
            rec_flag = curs.fetchall()
    finally:
        db.close()
        return rec_flag
    
# flage값이 1이면 동작, 0 또는 2이면 완료
#무한 반복 펌프 동작 유무 runflage = 1
#무한 반복 펌프 동작 중지 runstopflage = 1
#SD카드에서 데이터 읽기 sdreadflage = 1
#배기 펌프 동작 exhaustflage = 1
#흡기 펌프 동작 intakeflage = 1
#펌프 재시작 resetflage = 1
#펌프 동작 시간 설정 runtimeflage = 1
#ro 값 변경 roflage = 1
#scope 값 변경 scopeflage = 1
# sensorid부터 해서 총 10개의 자료를 받는다.
def db_check():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    curs = db.cursor()
    sql = 'SELECT  sensorid, runflage, runstopflage, sdreadflage, exhaustflage, intakeflage, resetflage, runtimeflage, roflage, scopeflage, runcount FROM sensoractiveconfig WHERE runflage = 1 or runstopflage = 1 or sdreadflage = 1 or exhaustflage = 1 or intakeflage = 1 or resetflage = 1 or runtimeflage = 1 or roflage = 1 or scopeflage = 1'
    curs.execute(sql)
    rowcounts = curs.rowcount()
    if rowcounts == 0:
        request_flag = 0
        return rowcounts, request_flag
    else:
        request_flag = curs.fetchall()
        return rowcounts, request_flag
    db.close()

def tick_result_check():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "SELECT ack_send FROM sensortickets WHERE s_flag=1".format(sensorid)
            curs.execute(sql)
            rowcounts = curs.rowcount()
            results = curs.fetchall()
    finally:
        return rowcounts, results
        db.close()
    
if __name__ == "__main__":
    while True:
        # sensorid부터 해서 총 10개의 자료를 받는다.
        rows, datas = db_check()
        if rows == 0:
            time.sleep(5)
            contiune
        else:
            for i in range(0,rows):
                for actions in datas:
                    sensorid = actions[i][0]
                    runflage = actions[i][1]
                    runstopflage= actions[i][2]
                    sdreadflage = actions[i][3]
                    exhaustflage = actions[i][4]
                    intakeflage = actions[i][5]
                    resetflage = actions[i][6]
                    runtimeflage = actions[i][7]
                    roflage = actions[i][8]
                    scopeflage = actions[i][9]
                    runcount = actions[i][10]
                    
                    if runflage == 1 and runcount >= 0 and runstopflage == 0 : send_request_data(sensorid)
                    elif sdreadflage == 1: read_request_sdcard(sensorid)
                    elif exhaustflage == 1: run_request_exhaust(sensorid)
                    elif intakeflage == 1: run_request_intake(sensorid)
                    elif resetflage == 1: reset_request_sensor(sensorid) #수동으로 리셋을 하는 경우
                    elif runtimeflage == 1:
                        runtime_setting_sensor(sensorid)
                        reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    elif roflage == 1:
                        ro_setting_sensor(sensorid)
                        reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                    else scopeflage == 1:
                        scope_setting_sensor(sensorid)
                        reset_request_sensor(sensorid) #설정하면 반드시 reset를 해야 적용된다
                time.sleep(3)
                
        # 처리 결과를 확인해서 응답이 있는 부분은 응답을 보낸다.
        rows, results = tick_result_check()
        for i in rows:
            write_ser.write(results.encode("utf-8"))
            app.logger.info('Command writting %s',results )
            SaveLog(results)
            time.sleep(3)
        time.sleep(5)
