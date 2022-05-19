import pymysql #MySQL 연결 위한 라이브러리

def get_pump_run_time(mode):
    db = pymysql.connect(host='localhost', user='root', password = 'atek21.com',db='sensordb')
    rundatatb = []
    try:
        with db.cursor() as curs:
            if mode == 'I':
                sql = "SELECT injections FROM pumprunntime"
            elif mode == 'P':
                sql = "SELECT fittimes FROM pumprunntime"
            elif mode == 'E':
                sql = "SELECT exjections FROM pumprunntime"
            curs.execute(sql)
            rundatatb = curs.fetchall()
    finally:
        db.close()
        return rundatatb
        
in_times = get_pump_run_time('I')
fi_times = get_pump_run_time('P')
ex_times = get_pump_run_time('E')

in_times = ''.join(in_times[0])
fi_times = ''.join(fi_times[0])
ex_times = ''.join(ex_times[0])
print(int(in_times), int(fi_times), int(ex_times))