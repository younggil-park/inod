#-*- coding:utf-8 -*-

import time
import datetime
import pymysql
import sys

def savecal1(sensorname, ro_value):
    try:
        nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
        cursor = db.cursor()
        sql = "INSERT INTO calibrationtb (sensorname, ro_value, checkdate) VALUES (%s,%s,%s)"
        data = (sensorname, ro_value,nowtime)
        cursor.execute(sql,data)
        db.commit()
    finally:
        db.close()

def savecal2(sensorname, level, x_side, y_side, scope):
    try:
        nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
        cursor = db.cursor()
        sql = "INSERT INTO calibrationtb (sensorname, level, x_side, y_side, scope, checkdate) VALUES (%s,%s,%s,%s,%s,%s)"
        data = (sensorname, level, x_side, y_side, scope, nowtime)
        cursor.execute(sql,data)
        db.commit()
    finally:
        db.close()
        
if __name__ == "__main__":
    
    MQLIST = ['MQ135', 'MQ136','MQ137','MQ138']
    RO=[+4.392,+3.927,+2.052,-2.818]
    Levels = [0,1,2,3]
    MQ135=[[0.999,-0.235,-0.472],[2.0,-0.707,-0.515],[2.305,-0.865,-0.504], [2.703,-1.065,-0.475]]
    MQ136=[[0.005,-0.241,-0.254],[1.013,-0.497,-0.269],[1.609,-0.656,-0.261],[1.976,-0.754,-0.272]]
    MQ137=[[0.003,-0.24,-0.262],[0.991,-0.499,-0.259],[1.666,-0.673,-0.274],[2.022,-0.771,-0.263]]
    MQ138=[[1.001,-0.287,-0.407],[1.689,-0.567,-0.538],[2.011,-0.74,-0.474],[2.287,-0.871,-0.421]]

    for datas in range(0,len(MQLIST)): #센서 이름
        sensorname = MQLIST[datas]
        ro_value = RO[datas]
        print('name={0}, ro={1:+07.3f}'.format(sensorname,ro_value))
        ro = '{0:+07.3f}'.format(ro_value)
        savecal1(sensorname, ro)
            
    for datas in MQLIST: #센서 이름
        sensorname = datas
        for lev in range(0, 4): # 레벨
            level = Levels[lev]
            #t = 'MQ13{0}[{1}][{2}]'.format(datas+5,datas,lev)[datas][lev]
            x_side = locals()[datas][lev][0]
            y_side = locals()[datas][lev][1]
            scope = locals()[datas][lev][2]
            print('name={0}, level={1}, x={2:+07.3f}, y={3:+07.3f}, scope={4:+07.3f}'.format(sensorname,level,x_side,y_side,scope))
            xx = '{0:+07.3f}'.format(x_side)
            yy = '{0:+07.3f}'.format(y_side)
            ss = '{0:+07.3f}'.format(scope)
            savecal2(sensorname, lev, xx, yy, ss)