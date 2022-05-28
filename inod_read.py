#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
from datetime import datetime
import datetime
import serial
import time
import pymysql #MySQL 연결 위한 라이브러리

#센서 데이터 수신 전용 모듈
serialPort2 = "/dev/ttyUSB1"
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
            if result1 != '':
                result2.append(result1)
                strResult = "".join(result2)
                
                # 처리 결과에 대한 수신은 cmdprocess 테이블과 tickets 테이블과 비교하여 결과 프래그만 세트한다. 
                if len(strResult) == 10:
                    strResult = strResult.split(',')
                    read_data_check(strResult)
                # 자동모드 데이터 수신 및 SD카드 데이터 수신에 대한 처리로 cmdprocess 테이블과 tickets 테이블과 비교하여 존재하면
                # 데이터를 저장하고 프래그를 세트
                elif len(strResult) >= 97:
                    strResult = strResult.split(',')
                    if len(strResult) == 13 and strResult[0][:3] == 'idx' and strResult[12] == 'etx' :
                        read_data_check(strResult)
                else:
                    continue
            else:  
                result1 = ""
        except UnicodeDecodeError:
            msg = 'Recive error UnicodeDecodeError'
            SaveLog(msg)
            continue
    SaveLog(msg)

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
def read_data_check(strResult):
    send_cmd_list = [',' ,'-' ,'W', 'I', 'P', 'E']
    read_cmd_list = ['2', 'I', 'P', 'E']
    read_datacmd_list = ['2', '3']
    sensordata = strResult[0]
    sensorid = sensordata[-1]
    respone_cmd = strResult[1]
    request_rows, request_cmd = get_cmdprocess(sensorid)
    if request_rows == 1 and  request_cmd != "None":
        #일반 및 설정 명령이면 응답 확인만 하고 f_flag 설정
        if request_cmd in send_cmd_list: 
            if respone_cmd in read_cmd_list:
                cmd_ticket_update(sensorid)
                SaveCmdResponseData(strResult)
                finish_update(sensorid)
        #센서 데이터 수집 및 SD카드 명령이면 응답 확인만 하고 f_flag 설정하든가 받았다고 응답만 하던가
        if request_cmd == '+': 
            if respone_cmd in read_datacmd_list: # f_flag 설정
                cmd_ticket_update(sensorid)
                SaveCmdResponseData(strResult)
                finish_update(sensorid)
            else:
                cmd_ticket_update(sensorid)
                SaveSensorData(strResult)
                SaveCmdResponseData(strResult)
        if request_cmd == ')':  # 센서 데이터 수집 저장하고 f_flag 설정
            cmd_ticket_update(sensorid)
            SaveSensorData(strResult)
            SaveCmdResponseData(strResult)
    else:
        msg = 'Not Found Send CMD....'
        SaveLog(msg)

def get_cmdprocess(sensorid):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "SELECT cmd FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.s_flag=1 and B.s_flag=1 and A.cmd=B.cmd".format(sensorid)
            curs.execute(sql)
            rows = curs.rowcount
            if rows == 1:
                cmds = curs.fetchall()
            else:
                cmds = "None"
    finally:
        return rows, cmds
        db.close()
        
def cmd_ticket_update(sensorid):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON (A.tickets = B.tickets) SET A.r_flag = 1, A.r_time = {0}, B.s_flag = 2, B.s_time = {0}  WHERE A.sensorid={1} and B.sensorid={1} and A.cmd=B.cmd".format(nowtime, sensorid)
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

#응답 로그 저장 
def SaveCmdResponseData(send_cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            curs.execute("INSERT INTO `sensorlog`  (`commands`, `InputDateTime`) VALUES (%s,%s)", (send_cmd,nowtime))
        db.commit()
    finally:
        db.close()


#최종 완료했다는 프래그
def finish_update(sensorid):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs: 
            sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON (A.tickets = B.tickets) SET A.f_flag = 1, A.f_time = {0}, B.s_flag=3 WHERE A.sensorid={1} and B.sensorid={1} and A.r_flag=1 and A.cmd=B.cmd and A.f_flag = 0".format(nowtime, sensorid)
            curs.execute(sql)
            db.commit()
                
    finally:
        db.close()
        
if __name__ == "__main__":
    while True:
        try:
            sensor_read_control()
        except KeyboardInterrupt:
            sys.exit()
