from datetime import datetime
import datetime
import serial
import time
import pymysql #MySQL ���� ���� ���̺귯��

#���� ������ ���� ���� ���
serialPort2 = "/dev/ttyUSB1"
read_ser = serial.Serial(serialPort2, baudrate=19200, timeout = 1)
read_ser.flushInput()

ack_send = ""
# �⺻ �����ʹ� ��� 10�ڸ� ����
# �����ʹ� 97�ڸ� ����
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
                
                # ���������� ���� ���� �� ���� �Ѵ�. �ڵ� ���� ���� ���� ����.
                # 1. SD ī�� �д� ��� �� �������� ���� ��� �˷��ָ� ���� �ڵ� ���� �α� ����(2), SD ī�� ����(3)
                if len(strResult) == 10: 
                    strResult = strResult.split(',')                     
                # �ڵ���� ������ ����, SDī�� ������ ����
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

# ���� ������ ����
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

#���� �α� ���� 
def SaveCmdResponseData(auto_send_cmd):
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    try:
        with db.cursor() as curs:
            curs.execute("INSERT INTO `sensorlog`  (`commands`, `InputDateTime`) VALUES (%s,%s)", (auto_send_cmd,nowtime))
        db.commit()
    finally:
        db.close()

#��� ���� ó�� ��� ���� 
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