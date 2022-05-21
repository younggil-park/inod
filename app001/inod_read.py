from datetime import datetime
import datetime
import serial
import time
import pymysql #MySQL 연결 위한 라이브러리

#센서 데이터 수신 전용 모듈
#serialPort2 = "/dev/ttyUSB1"
#read_ser = serial.Serial(serialPort2, baudrate=19200, timeout = 1)
#read_ser.flushInput()

ack_send = ""
#프로그램 전체 흐름 설명
#수신데이테를 읽는다.
# 데이터의 크기를 비교하여 단순 응답처리인지 데이터 수신인질 확인한다.
# cmdprocess와 ticket 테이블의 정보가 일치 하는지를 확인다. 존재하는지 그리고 티켓이 있는지
# 다음으로 발행 티켓의처리를 완료했다는 결과 처리를 하고, 동작설정부분을 클리어한다.
# 데이터 수신의 경우 반복작업에 대한 처리를 생각하여야 한다
# 그리고 설정의 경우 반복 작업을 생각하여야 한다.

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
                    # 입력받은 자료를 명령이 전달된것인지 확인하고 업데이트를 한다.
                    cmd_ticket_compare_and_update(strResult)
                    SaveCmdResponseData(strResult)
                # 자동모드 데이터 수신 및 SD카드 데이터 수신에 대한 처리로 cmdprocess 테이블과 tickets 테이블과 비교하여 존재하면
                # 데이터를 저장하고 프래그를 세트
                elif len(strResult) >= 97:
                    strResult = strResult.split(',')
                    if len(strResult) == 13 and strResult[0][:3] == 'idx' and strResult[12] == 'etx' :
                        # 입력받은 자료를 명령이 전달된것인지 확인하고 업데이트를 한다.
                        cmd_ticket_compare_and_update(strResult)
                        SaveSensorData(strResult)
                        SaveCmdResponseData(strResult)
                else:
                    continue
            else:  
                result1 = ""
        except UnicodeDecodeError:
            msg = 'Recive error UnicodeDecodeError'
            SaveLog(msg)
            continue
    SaveLog(msg)

def cmd_ticket_compare_and_update(revPacket):
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
                
            sql = "SELECT * FROM cmdprocess A INNER JOIN  sensortickets B ON A.tickets = B.tickets WHERE A.sensorid={0} and B.sensorid={0} and A.s_flag=1 and B.s_flag=1".format(id_value)
            curs.execute(sql)
            rows = curs.rowcount()
            if rows == 1:
                sql = "UPDATE cmdprocess A INNER JOIN  sensortickets B ON (A.tickets = B.tickets) SET A.r_flag = 1, A.r_time = {0}, B.s_flag = 1 , B.s_time = {1}  WHERE A.sensorid={2} and B.sensorid={2}".format(now(), now(), id_value)
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
    
if __name__ == "__main__":
    while True:
        sensor_read_control()
