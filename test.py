#-*- coding:utf-8 -*-
import pymysql #MySQL 연결 위한 라이브러리

def get_rotb():
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rodatatb = []
    try:
        with db.cursor() as curs:
            sql = "SELECT SensorName, RO_Value FROM cal_ro_tb"
            curs.execute(sql)
            rodatatb = curs.fetchall()
    finally:
        db.close()
        return rodatatb

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
        
rotb = get_rotb()
mq135_ro = rotb[0]
mq136_ro = rotb[1]
mq137_ro = rotb[2]
mq138_ro = rotb[3]
ro_data = '{0},{1},{2},{3}'.format(mq135_ro[1],mq136_ro[1],mq137_ro[1],mq138_ro[1])

scopetb = get_scopetb()
mq135_scope0 = scopetb[0]
mq135_scope1 = scopetb[1]
mq135_scope2 = scopetb[2]
mq135_scope3 = scopetb[3]
mq136_scope0 = scopetb[4]
mq136_scope1 = scopetb[5]
mq136_scope2 = scopetb[6]
mq136_scope3 = scopetb[7]
mq137_scope0 = scopetb[8]
mq137_scope1 = scopetb[9]
mq137_scope2 = scopetb[10]
mq137_scope3 = scopetb[11]
mq138_scope0 = scopetb[12]
mq138_scope1 = scopetb[13]
mq138_scope2 = scopetb[14]
mq138_scope3 = scopetb[15]

mq135_level0 = '{0},{1},{2}'.format(mq135_scope0[2],mq135_scope0[3],mq135_scope0[4])
mq135_level1 = '{0},{1},{2}'.format(mq135_scope1[2],mq135_scope1[3],mq135_scope1[4])
mq135_level2 = '{0},{1},{2}'.format(mq135_scope2[2],mq135_scope2[3],mq135_scope2[4])
mq135_level3 = '{0},{1},{2}'.format(mq135_scope3[2],mq135_scope3[3],mq135_scope3[4])
mq136_level0 = '{0},{1},{2}'.format(mq136_scope0[2],mq136_scope0[3],mq136_scope0[4])
mq136_level1 = '{0},{1},{2}'.format(mq136_scope1[2],mq136_scope1[3],mq136_scope1[4])
mq136_level2 = '{0},{1},{2}'.format(mq136_scope2[2],mq136_scope2[3],mq136_scope2[4])
mq136_level3 = '{0},{1},{2}'.format(mq136_scope3[2],mq136_scope3[3],mq136_scope3[4])
mq137_level0 = '{0},{1},{2}'.format(mq137_scope0[2],mq137_scope0[3],mq137_scope0[4])
mq137_level1 = '{0},{1},{2}'.format(mq137_scope1[2],mq137_scope1[3],mq137_scope1[4])
mq137_level2 = '{0},{1},{2}'.format(mq137_scope2[2],mq137_scope2[3],mq137_scope2[4])
mq137_level3 = '{0},{1},{2}'.format(mq137_scope3[2],mq137_scope3[3],mq137_scope3[4])
mq138_level0 = '{0},{1},{2}'.format(mq138_scope0[2],mq138_scope0[3],mq138_scope0[4])
mq138_level1 = '{0},{1},{2}'.format(mq138_scope1[2],mq138_scope1[3],mq138_scope1[4])
mq138_level2 = '{0},{1},{2}'.format(mq138_scope2[2],mq138_scope2[3],mq138_scope2[4])
mq138_level3 = '{0},{1},{2}'.format(mq138_scope3[2],mq138_scope3[3],mq138_scope3[4])
