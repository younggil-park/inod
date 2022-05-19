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

def saveDB(revPacket):
    data_value = revPacket
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    #app.logger.info('SaveDB %s',revPacket)
    try:
        with db.cursor() as curs:
            idVal = data_value[0]
            if len(idVal) == 4:
                id_value = idVal[-1]
            else:
                id_value = idVal[0]
                
            sql = """INSERT INTO sensordata (sensorID, H2, H2S, NH3, Toluene, CO2, VOC, CO, Temp1, Temp2, Hum1, Hum2, InputDateTime) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            data = (id_value,data_value[1],data_value[2],data_value[3],data_value[4],data_value[5], data_value[6],data_value[7],data_value[8],data_value[9],data_value[10],data_value[11],nowtime)
            curs.execute(sql,data)
        db.commit()
    finally:
        db.close()
        
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
def get_pump_run_time(sensor_id, mode):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rundatatb = []
    try:
        with db.cursor() as curs:
            if mode == 'I':
                sql = "SELECT injections FROM pumprunntime where nos = {}".format(sensor_id)
            elif mode == 'P':
                sql = "SELECT fittimes FROM pumprunntime where nos = {}".format(sensor_id)
            elif mode == 'E':
                sql = "SELECT exjections FROM pumprunntime where nos = {}".format(sensor_id)
            curs.execute(sql)
            rundatatb = curs.fetchall()
    finally:
        db.close()
        return rundatatb
        
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

# 펌프 동작 시간 변경 요청: idx1, I|P|E (대문자),XXXXX,etx -16자리
#def pump_run_config_reset(sensor_ids, mode, runningtimes):
def pump_run_config_reset(sensor_ids, runningtimes):
    for sensor_id in range(0, len(sensor_ids)):
        checktime = 0
        runtimes1 = '{0:05d}'.format(runningtimes[0])
        runtimes2 = '{0:05d}'.format(runningtimes[1])
        runtimes3 = '{0:05d}'.format(runningtimes[2])
		
        ack_send = "0"
        pp_set = 'idx{0},I,{1},etx'.format(sensor_ids[sensor_id], runtimes1)
		sendProcessFunction(sensor_ids[sensor_id], 'I', pp_set, ack_send)
		time.sleep(5)
		
        pp_set = 'idx{0},P,{1},etx'.format(sensor_ids[sensor_id], runtimes2)
		sendProcessFunction(sensor_ids[sensor_id], 'P', pp_set, ack_send)
		time.sleep(5)
		
        pp_set = 'idx{0},E,{1},etx'.format(sensor_ids[sensor_id], runtimes3)
        sendProcessFunction(sensor_ids[sensor_id], 'E', pp_set, ack_send)
		time.sleep(5)
		
        #DB save
        set_pump_run_time(sensor_ids[sensor_id],'I',runtimes1)
        set_pump_run_time(sensor_ids[sensor_id],'P',runtimes2)
        set_pump_run_time(sensor_ids[sensor_id],'E',runtimes3)

        time.sleep(5)
    #모든 센서에 동작 시간 설정이 완료되면 재시작해야 설정된 값이 적용됨
    config_reset(sensor_ids)
        
# Ro값 변경 요청: idx1, W(대문자),5(6|7|8),A,Ro값,,,etx)-32자리
def config_reset(sensor_ids):
    for sensor_id in range(0, len(sensor_ids)):
        checktime = 0
        ro_send = 'idx{0},R,etx'.format(sensor_ids[sensor_id])
        ack_send = "0"
        sendProcessFunction(sensor_ids[sensor_id], 'R', ro_send, ack_send)
        msg = ' Reset CMD SensorID:{0}, CMD:{1}'.format(sensor_ids[sensor_id], ro_send)
        app.logger.info('Command writting %s',msg )
        SaveLog(msg)
        while (checktime < 10):
            time.sleep(1)
            checktime += 1
            app.logger.info('Rebooting.. %s',checktime)
           
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
            sendProcessFunction(sensor_ids[sensor_id], 'W', ro_send, ack_send)
            i += 1
    #모든 센서에 동작 시간 설정이 완료되면 재시작해야 설정된 값이 적용됨
    config_reset(sensor_ids)
    
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
                sendProcessFunction(sensor_ids[sensor_id], 'W', scope_send, ack_send)
	#모든 센서에 동작 시간 설정이 완료되면 재시작해야 설정된 값이 적용됨
    config_reset(sensor_ids)
    
def autorun_sensor(runcount, sensor_ids, cycle_time):
    countcheck = 0
    app.logger.info('1-1.auto run %s select sensor count %s Sensors Nos %s',runcount, len(sensor_ids), sensor_ids)
    today = datetime.datetime.now()
    years = today.year
    months = today.month
    days = today.day
    hours = today.hour
    minutes = today.minute
    seconds = today.second
    cnt = 0
    
    if runcount == 0: # 무한 루푸 선택
        while True:
            flags1 = config_flag(1,1) # 오토모드 프래그 확인 (1 종료, 0은 계속) 튜플타입 디비에서 갖고 오도록 한것
            msg = 'auto_run_stop flags: {0}'.format(flags1[0])
            app.logger.info('auto_run_stop flags: %s',msg)
            if int(flags1[0]) == 1:
                break #종료해라
            for sensor_id in range(0, len(sensor_ids)):
                cnt = 0
                auto_send_cmd = 'idx{0},),{1:02d},{2:02d},{3:02d},{4:02d},{5:02d},{6:02d},etx'.format(sensor_ids[sensor_id], years, months, days, hours,minutes, seconds)
                app.logger.info('1-1-2.autorun sensor No %s count %s cmd %s',sensor_ids[sensor_id], countcheck, auto_send_cmd)
                ack_send = 'idx{0},1,etx'.format(sensor_ids[sensor_id])
                
                # 명령어 요청시 티켓을 생성하여 확인한다.
                sendProcessFunction(sensor_ids[sensor_id], ')', auto_send_cmd, ack_send)
                
            countcheck += 1     

            if int(flags1[0]) == 1:
                msg = 'auto run flag:{0}'.format(flags1[0])
                #SaveLog(msg)
                app.logger.info(msg)
                break

            cnt = 0
            for i in range(0, cycle_time * 60): # 다음 센서 읽는 주기
                time.sleep(1)
                cnt = cnt + 1
                app.logger.info(" Next Sensing Waiting time...%s",cnt)
        
    else: # 무한 루푸가 아닌 경우
        for run_cnt in range(0, runcount): #횟수를 정의한경우(1부터~)
            for sensor_id in range(0, len(sensor_ids)):
                auto_send_cmd = 'idx{0},),{1:02d},{2:02d},{3:02d},{4:02d},{5:02d},{6:02d},etx'.format(sensor_ids[sensor_id],years,months,days,hours,minutes,seconds)

                ack_send = 'idx{0},1,etx'.format(sensor_ids[sensor_id])
                # 명령어 요청시 티켓을 생성하여 확인한다.
                sendProcessFunction(sensor_ids[sensor_id], ')', auto_send_cmd,ack_send)
                msg = 'count run counter={0}'.format(run_cnt)
                cnt = 0
            for i in range(0, cycle_time * 60): # 다음 센서 읽는 주기
                time.sleep(1)
                cnt = cnt + 1
                app.logger.info(" Next Sensing Waiting time...%s",cnt)
        msg = 'count run {0}'.format(runcount)
    msg = 'Sensor running stoped..{0}'.format(msg)
    SaveLog(msg)
    #app.logger.info(msg)
    return msg
    
# SD카드에 있는 데이터 전송 요청 idx1,+,etx 
def recived_sd_data(sensor_ids):
    for sensor_id in range(0, sensor_ids):
        sd_send = 'idx{0},+,etx'.format(sensor_id)
        #app.logger.info('sd send data %s',sd_send)
        ack_send = 'idx{0},1,etx'.format(sensor_id)
        # 명령어 요청시 티켓을 생성하여 확인한다.
        sendProcessFunction(sensor_id, '+', sd_send, ack_send)
        
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
    create_request_ticket(sensor_id, cmd, ack_send, new_tickets)
	InsertcmdProcess(sensorid, cmd, new_ticket)
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
'''
# 명령처리 완료 유무와 티켓 생성을 처리한다.
def create_request_ticket(sensor_id, cmd, ack_send, new_tickets):
	nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "INSERT INTO  sensortickets  (SENSORID, CMD, ACK_SEND, TICKETS, S_FLAGE, S_TIME) VALUES({0},{1},{2},{3})".format(sensorid, cmd, ack_send, new_tickets, 0, nowtime)
            curs.execute(str_query)
        db.commit()
    finally:
        db.close()

'''
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
def InsertcmdProcess(sensorid, cmd, new_tickets):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            str_query = "INSERT INTO  cmdprocess  (SENSORID, CMD, TICKETS, S_FLAGE, S_TIME) VALUES({0},{1},{2},{3})".format(sensorid, cmd, new_tickets, 1, nowtime)
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
            str_query = "SELECT r_flag FROM  cmdprocess  WHERE SID={0} AND CMD={1} AND S_FLAG={2}".format(sensorid, cmd, 0)
            curs.execute(str_query)
            rec_flag = curs.fetchall()
    finally:
        db.close()
        return rec_flag
		
# 서버에서 배기 요청(idx1,,,etx)-10자리
def export_pump_run(sensor_ids):
    for sensor_id in range(0, len(sensor_ids)):
        sd_send = 'idx{0},,,etx'.format(sensor_ids[sensor_id])
        #app.logger.info('export send data %s',export_send)
        ack_send = "0"
        sendProcessFunction(sensor_id, ',', sd_send, ack_send)

# 서버에서 흡기 요청(idx1,-,etx)-10자리
def import_pump_run(sensor_ids):
    for sensor_id in range(0, len(sensor_ids)):
        sd_send = 'idx{0},-,etx'.format(sensor_ids[sensor_id])
        #app.logger.info('import send data %s',import_send)
        ack_send = "0"
        sendProcessFunction(sensor_id, '-', sd_send, ack_send)

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
    app.logger.info('1-1-2.autorun sensor No %s count %s cmd %s',sensor_ids[sensor_id], countcheck, auto_send_cmd)
    ack_send = 'idx{0},1,etx'.format(sensor_ids[sensor_id])
    
    # 명령어 요청시 티켓을 생성하여 확인한다.
    sendProcessFunction(sensor_ids[sensor_id], ')', auto_send_cmd, ack_send)
    
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
	sql = 'SELECT  sensorid, runflage, runstopflage, sdreadflage, exhaustflage, intakeflage, resetflage, runtimeflage, roflage, scopeflage FROM sensoractiveconfig WHERE runflage = 1 or runstopflage = 1 or sdreadflage = 1 or exhaustflage = 1 or intakeflage = 1 or resetflage = 1 or runtimeflage = 1 or roflage = 1 or scopeflage = 1'
	curs.execute(sql)
    rowcounts = curs.rowcount()
    if rowcounts == 0:
        request_flag = 0
        return rowcounts, request_flag
    else:
        request_flag = curs.fetchall()
        return rowcounts, request_flag
    db.close()
	
	
if __name__ == "__main__":
	while True:
        # sensorid부터 해서 총 10개의 자료를 받는다.
		rows, datas = db_check()
        if rows == 0:
            contiune
        else:
            for i in range(0,rows):
                for actions in datas:
                    sensorid = actions[i][0]
                    runflage = actions[i][1]
                    runstopflage = actions[i][2]
                    sdreadflage = actions[i][3]
                    exhaustflage = actions[i][4]
                    intakeflage = actions[i][5]
                    resetflage = actions[i][6]
                    runtimeflage = actions[i][7]
                    roflage = actions[i][8]
                    scopeflage = actions[i][9]
                    
                    if runflage == 1: send_request_data(sensorid)
                    elif runstopflage == 1: stop_request_sensor(sensorid)
                    elif sdreadflage == 1: read_request_sdcard(sensorid)
                    elif exhaustflage == 1: run_request_exhaust(sensorid)
                    elif intakeflage == 1: run_request_intake(sensorid)
                    elif resetflage == 1: reset_request_sensor(sensorid)
                    elif runtimeflage == 1: runtime_setting_sensor(sensorid)
                    elif roflage == 1: ro_setting_sensor(sensorid)
                    else scopeflage == 1: scope_setting_sensor(sensorid)
                time.sleep(5)
        time.sleep(5)