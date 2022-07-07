#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
from datetime import datetime
import datetime
import serial
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

#센서 데이터 수신 전용 모듈
serialPort2 = "/dev/ttyUSB0"
read_ser = serial.Serial(serialPort2, baudrate=19200, timeout = 1)
read_ser.flushInput()

ack_send = ""
#프로그램 전체 흐름 설명
#수신데이테를 읽는다.
# 데이터의 크기를 비교하여 단순 응답처리인지 데이터 수신인질 확인한다.
# cmdprocess와 ticket 테이블의 정보가 일치 하는지를 확인다. 존재하는지 그리고 티켓이 있는지
# 다음으로 발행 티켓의처리를 완료했다는 결과 처리를 하고, 동작설정부분을 클리어한다.
# 데이터 수신의 경우 반복작업에 대한 처리를 생각하여야 한다
# 그리고 설정의 경우 반복 작업을 생각하여야 한다.

# 기본 데이터는 모두 10자리 응답
# 데이터는 97자리 응답
def sensor_read_control():
    result2 = []
    checktime = 0
    strStatus = ''
    while True:
        try:
            result1 = read_ser.readline().decode('utf-8') 
            #msg = "read checking... ".format(result1)
            #logger.info('sensor_read_control func: %s',msg )
            if result1 != '':
                result2.append(result1)
                strResult = "".join(result2)
                msg = " data  {0} ".format(strResult)
                logger.info('sensor_read_control func: read_raw: %s',msg )
                # 처리 결과에 대한 수신은 cmdprocess 테이블과 tickets 테이블과 비교하여 결과 프래그만 세트한다. 
                if len(strResult) == 10:
                    org_data = strResult
                    strResult = strResult.split(',')
                    msg = "data  {0} ".format(strResult)
                    logger.info('sensor Response Resultmsg: %s',msg )
                    read_data_check(strResult, org_data)
                # 자동모드 데이터 수신 및 SD카드 데이터 수신에 대한 처리로 cmdprocess 테이블과 tickets 테이블과 비교하여 존재하면
                # 데이터를 저장하고 프래그를 세트
                elif len(strResult) >= 97:
                    org_data = strResult
                    strResult = strResult.split(',')
                    if len(strResult) == 15 and strResult[0][:3] == 'idx' and strResult[12][0:3] == 'etx' :
                        del strResult[13: ]
                        strResult[12] = strResult[12][0:3]
                        msg = "data  {0} ".format(strResult)
                        logger.info('Sensor Data Resultmsg: %s',msg )
                        read_data_check(strResult,  org_data)
                    if len(strResult) == 13 and strResult[0][:3] == 'idx' and strResult[12] == 'etx' :
                        msg = "data  {0} ".format(strResult)
                        logger.info('Sensor Data Resultmsg: %s',msg )
                        read_data_check(strResult,  org_data)
                else:
                    result2 = []
                    continue
            else:
                result2 = []
                result1 = ""
        except UnicodeDecodeError:
            msg = 'Recive error UnicodeDecodeError'
            SaveCmdResponseData(msg)
            continue
        time.sleep(1)
    SaveCmdResponseData(msg)

# 읽어 들인 자료에 대하여 응답인지 등등을 검사하여 처리
# 보낸 명령어에 대한 응답 명령어를 확인하여 처리한다.
# 센서 데이터 읽기와 SD 카드 데이터 읽기 부분은 명령어와 결과 값에 따라 완료 하던가 계속 유지하는 작업이 필요하고
# 그외 요청에 대한 응답과 명령어 확인하여 완료를 확인한다.
'''
서버:데이터요청  )        -> 센서:데이터생성 보냄                   -> 서버:응답 idx0,1,etx
서버:로그요청    +         -> 센서:데이터있으면 보냄                ->서버:응답 idx0,1,etx
                                   센서: 데이터없으면 응답 idx0,2,etx
                                   센서: SD에러면 응답 idx0,3,etx
서버:배기요청     ,        -> 센서: 응답 idx0,2,etx
서버:흡기요청      -       -> 센서: 응답 idx0,2,etx
서버:RO설정요청  W       ->센서: 모두 수신후 응답 idx0,2,etx
서버:SCope설정요청  W   ->센서: 모두 수신후 응답 idx0,2,etx
서버:흡입시간요청  I     -> 센서: 시간값으로 응답 idx0,I,00780,etx
서버:온도보정시간요청 P -> 센서: 시간값으로 응답 idx0,P,00010,etx
서버:배기시간요청      E -> 센서: 시간값으로 응답 idx0,E,00030,etx
'''
def read_data_check(strResult, org_data):
    send_cmd_list = ['ca' ,'dh' ,'W', 'I', 'P', 'E']
    read_cmd_list = ['2', 'I', 'P', 'E']
    read_datacmd_list = ['2', '3']
    sensordata = strResult[0]
    sensorid = sensordata[-1]
    respone_cmd = strResult[1]
    #해당 센서의 명령 갯수, 명령어 그리고 티켓을 받아와서 명령어에 대한 결과 처리를 하도록 한다.
    #무한 반복과 일정 회수 반복의 경우 데이터을 받으면 받았다는 응답을 10초 이내에 해야 한다. 
    #그런데 응답을 하지 않으면 SD 카드에 저장한다는 3번 메세지를 보낸다.(확인 해봐야 한다. 개발자에게)
    request_rows, request_cmd, request_tickets = get_cmdprocess(sensorid)

    if request_rows == 1 and  request_cmd != "None":
        #일반 및 설정 명령이면 응답 확인만 하고 f_flag 설정
        if request_cmd in send_cmd_list:
            if respone_cmd in read_cmd_list:
                cmd_ticket_update(sensorid, request_cmd, request_tickets)
                SaveCmdResponseData(org_data)
                finish_update(sensorid, request_tickets)

        #SD카드 명령이면 응답 확인만 하고 f_flag 설정하든가 받았다고 응답만 하던가
        #데이터 없으면 2를 센서가 보낸다. SD카드 불량이면 3을 센서가 보낸다.
        if request_cmd == 'ps':
            if respone_cmd in read_datacmd_list: # f_flag 설정 (2,3)이면 종료
                cmd_ticket_update(sensorid, request_cmd, request_tickets)
                SaveCmdResponseData(org_data)
            else:
                cmd_ticket_update(sensorid, request_cmd, request_tickets)
                SaveCmdResponseData(org_data)
                SaveSensorData(strResult)
                response_ack_send(sensorid, request_tickets)
            finish_update(sensorid, request_tickets)
                
         # 센서 데이터 수집 저장하고 카운터 또는 무한 모드일경우에 대한 처리가 필요하다.
        if request_cmd == 'bt':
            cmd_ticket_update(sensorid, request_cmd, request_tickets)
            SaveCmdResponseData(org_data)
            SaveSensorData(strResult) 
            response_ack_send(sensorid, request_tickets)
            #펌프 배기시간을 체크해야 한다.
            run_flage_setting(sensorid)
            #finish_update(sensorid, request_tickets)
    else:
        msg = 'Not Found Send CMD....'
        SaveCmdResponseData(msg)

# 자동모드와 카드 읽기 모드의 경우 해당 센서에 응답을 보내야 하는 값이 있으면
# 처리하도록 한다. read에서 SD 카드에 대한 2,3 값을 받으면 ack_send를 0으로 처리하기때문에
# 0이 아니면 명령을 보낸다.
def response_ack_send(sensorid, request_tickets):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    results = "ACK Not found"
    rows = 0
    try:
        with db.cursor() as curs:
            sql = "SELECT B.ack_send FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.s_flag=1 and A.r_flag=1 and A.f_flag = 0 and B.s_flag=2 and A.cmd=B.cmd and A.tickets = '{1}' and B.tickets = '{1}'".format(sensorid, request_tickets)
            curs.execute(sql)
            rows = curs.rowcount
            if rows == 1:
                results = list(curs.fetchone())
                results = results[0]
                msg = " : row={0}, result={1}".format(rows, results)
                logger.info('send response message: %s',msg )
                read_ser.write(results.encode("utf-8"))
    finally:
        db.close()
        SaveCmdResponseData(results)
        
#센서에서 받은 데이터에서 센서 아이디를 받아서 해당 센서에 요청한 명령어와 티켓 번호를 전달하기위한 함수
def get_cmdprocess(sensorid):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "SELECT A.cmd, A.tickets FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.s_flag=1 and B.s_flag=1 and A.r_flag=0 and A.f_flag=0".format(sensorid)
            curs.execute(sql)
            rows = curs.rowcount
            if rows == 1:
                r_cmds = list(curs.fetchall())
                cmds = r_cmds[0][0]
                tickets = r_cmds[0][1]
            else:
                cmds = "None"
                r_cmds = "None2"
                tickets = "None"
            msg = "sensorid={0}, row={1}, all_select={3}, cmds={2}, tickets = {4}".format(sensorid, rows, cmds, r_cmds, tickets)
            logger.info('get cmd and tickets: %s',msg )
    finally:
        return rows, cmds, tickets
        db.close()
        
# cmd와 티켓 테이블의 프래그를 업데이트한다.        
def cmd_ticket_update(sensorid, request_cmd, request_tickets):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets SET A.r_flag = 1, A.r_time = '{0}', B.s_flag = 2, B.s_time = '{0}' WHERE A.sensorid={1} and B.sensorid={1} and A.cmd='{2}' and B.cmd='{2}' and A.r_flag = 0 and A.f_flag = 0 and A.tickets = '{3}' and B.tickets = '{3}'".format(nowtime, sensorid, request_cmd, request_tickets)
            curs.execute(sql)
            db.commit()
                
    finally:
        db.close()
        
# 센싱 데이터 저장
def SaveSensorData(revPacket):
    data_value = revPacket
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            idVal = data_value[0]
            id_value = idVal[-1]
                
            sql = """INSERT INTO sensordata (sensorID, H2, H2S, NH3, Toluene, CO2, VOC, CO, Temp1, Temp2, Hum1, Hum2, InputDateTime) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            data = (id_value,data_value[1],data_value[2],data_value[3],data_value[4],data_value[5], data_value[6],data_value[7],data_value[8],data_value[9],data_value[10],data_value[11],nowtime)
            curs.execute(sql,data)
            db.commit()
    finally:
        db.close()

# sensoractiveconfig 테이블에 펌프 동작시간(핏팅 + 배기시간) 추가하고, 동작 프래그를 3으로 설정하여 동작시간 대기처리를 한다.
def run_flage_setting(sensorid):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            #무한 동작이나 카운터 동작의 경우 flage는 3로 해야 한다. 펌프 동작 시간 대기하고 다시 runflage = 1로 세팅해야
            #send에서 데이터를 요구한다.
            sql = 'UPDATE sensoractiveconfig A, sensorpumpruntime B SET A.runtimecheck = B.fittimes + B.exhausttimes, A.runflage = 3 WHERE A.sensorid = {0} and B.sensorid = {0}'.format(sensorid)
            curs.execute(sql)
            db.commit()
    finally:
        db.close()
        
#응답 로그 저장 
def SaveCmdResponseData(send_cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "INSERT INTO sensorlog  (commands, InputDateTime) VALUES ('{0}', '{1}')".format(send_cmd,nowtime)
            curs.execute(sql)
        db.commit()
    finally:
        db.close()


#최종 완료했다는 프래그
def finish_update(sensorid, request_tickets):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs: 
            sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON (A.tickets = B.tickets) SET A.f_flag = 1, A.f_time = '{0}', B.s_flag=3, B.s_time = '{0}'  WHERE A.sensorid={1} and B.sensorid={1} and A.r_flag=1 and B.s_flag=2 and A.cmd=B.cmd and A.tickets = '{2}' and B.tickets = '{2}'".format(nowtime, sensorid, request_tickets)
            curs.execute(sql)
            db.commit()
            
    finally:
        db.close()
        
if __name__ == "__main__":
    logger.info('This program is an inod_read program that read data.' )
    logger.info('Check if there is data to read, and if there is data, read it.' )
    while True:
        try:
            sensor_read_control()
        except KeyboardInterrupt:
            sys.exit()
