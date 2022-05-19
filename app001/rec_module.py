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
# 기본 데이터는 모두 10자리 응답
# 데이터는 97자리 응답
def Serial_control():
    result2 = []
    checktime = 0
    strStatus = ''
    while True:
        try:
            result1 = read_ser.readline().decode('utf-8') 
            if result1 != '':
                result2.append(result1)
                strResult = "".join(result2)
                
                # 센서에서의 응답 수신 만 존재 한다. 자동 모드는 응답 수신 없다.
                # 1. SD 카드 읽는 명령 후 서버에서 받은 결과 알려주면 응답 코드 저장 로그 없음(2), SD 카드 에러(3)
                if len(strResult) == 10: 
                    strResult = strResult.split(',')                     
                # 자동모드 데이터 수신, SD카드 데이터 수신
                elif len(strResult) >= 97:
                    strResult = strResult.split(',')
                    if len(strResult) == 13 and strResult[0][:3] == 'idx' and strResult[12] == 'etx' :
                        saveDB(strResult)
                        SaveLog(ack_send)
                else:
                    continue
            else:  
                result1 = ""
        except UnicodeDecodeError:
            msg = 'Recive error UnicodeDecodeError'
            SaveLog(msg)
            continue
    SaveLog(msg)

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
def SaveCmdResponseData(auto_send_cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            curs.execute("INSERT INTO `sensorlog`  (`commands`, `InputDateTime`) VALUES (%s,%s)", (auto_send_cmd,nowtime))
        db.commit()
    finally:
        db.close()

#명령 응답 처리 결과 저장 
def UpdateCmdProcess(sensorid, cmd, flage):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
			str_query = "UPDATE  cmdprocess  SET flage={0}, r_time={1} WHERE SID={2} AND CMD={3} AND flage=0".format(flage,nowtime,sensorid,cmd)
            curs.execute(str_query)
        db.commit()
    finally:
        db.close()
	
if __name__ == "__main__":
	while True:
		Serial_control()
