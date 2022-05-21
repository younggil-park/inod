#-*- coding:utf-8 -*-

from flask import render_template, request, redirect, url_for, session, jsonify, flash, send_file, make_response
import re
from app001 import app
from app001.models import User
import bcrypt
#import socket
#from datetime import datetime
#import datetime
from flask import Response
import time
import sys
import struct
import logging
from app001 import web_dbsave
app.secret_key = 'atek21.com'
      
# ---------- 함수 정의 부분 끝  ----
# .errorhandler(에러코드) : flask 내부에 기본적으로 있는 에러 핸들러
# 특정 에러에 대하여 errorhandler를 사용하면, 해당 에러가 발생했을 때 매칭된다.
@app.errorhandler(404)
def page_not_found(error):
    #app.logger.error(error)
    return render_template('error.html')

@app.errorhandler(500)
def internal_error(error):
    #app.logger.error(error)
    return render_template('400.html')
    
#메인 페이지 처리 
@app.route("/")
def main():
    if session.get('logged_in'):
        return render_template('loggedin.html')
    else:
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])        
@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''
    # username과 password에 입력값이 있을 경우
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # 쉬운 checking을 위해 변수에 값 넣기
        username = request.form['username']
        password = request.form['password']
        account, check_password = User.login_check(username, password)
        if account != "None":
            # 정상적으로 유저가 있으면 새로운 세션 만들고, 없으면 로그인 실패 문구 출력하며 index 리다이렉트
            if check_password:
                fromip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                nowcontime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['logintime'] =  nowcontime
                session['userip'] =  fromip
                
                loginuserinfo = 'login info: id:{0}, user:{1},client ip:{2}, logintime:{3}'.format(account['id'], account['username'], fromip, nowcontime)
                web_dbsave.SaveLog(loginuserinfo)
                User.update_fromip(fromip, account['id'])
                return redirect(url_for('home'))
        else:
            msg = '사용자 없거나 정보가 잘못되었은 확인 바랍니다.'
    if 'loggedin' in session:
        return redirect(url_for('home'))
    return render_template('index.html', msg=msg)

@app.route('/home', methods=['POST','GET'])
@app.route('/home/', methods=['POST','GET'])
def home():
    # Check if user is loggedin
    msg = '각종 제어 설정 부분입니다.'
    sentb =[0]
    if 'loggedin' in session:
        if request.method == 'POST':
            msg = request.form['msg']
        else:
            msg = request.args.get('msg')
            
        sentb = web_dbsave.get_sensortb()

        msg_sensordata = 'ID:{0}, H2:{1}, H2S:{2}, NH3:{3}, Tol:{4}, CO2:{5}, VOC:{6}, CO:{7}, TH1:{8}, TH2:{9}, RH1:{10}, RH2:{11}'.format(sentb[0],sentb[1],sentb[2],sentb[3],sentb[4],sentb[5],sentb[6],sentb[7],sentb[8],sentb[9],sentb[10],sentb[11])
        
        # runningtime 테이블에서 읽어서 화면에 표출
        runtimetb = web_dbsave.get_runtimetb()
        intaketimes = runtimetb[0][0]
        fittimes = runtimetb[0][1]
        exhausttimes = runtimetb[0][2]
        
        # RO / Scope 테이블에서 읽어서 화면에 표출
        rotb = web_dbsave.get_rotb()
        mq135_ro = rotb[0]
        mq136_ro = rotb[1]
        mq137_ro = rotb[2]
        mq138_ro = rotb[3]
        rol1 = '+{0}'.format(mq135_ro[1])
        rol2 = '+{0}'.format(mq136_ro[1])
        rol3 = '+{0}'.format(mq137_ro[1])
        rol4 = '+{0}'.format(mq138_ro[1])

        scopetb = web_dbsave.get_scopetb()
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
        ip_addr = request.environ['SERVER_NAME']
        flash(ip_addr)
        
        return render_template('home.html', username=session['username'], logintime=session['logintime'], userip=session['userip'], myip_addr=ip_addr, msg=msg, sendata=msg_sensordata, ro1=rol1,ro2=rol2,ro3=rol3,ro4=rol4,s0=mq135_level0,s1=mq135_level1,s2=mq135_level2,s3=mq135_level3,y0=mq136_level0,y1=mq136_level1,y2=mq136_level2,y3=mq136_level3,u0=mq137_level0,u1=mq137_level1,u2=mq137_level2,u3=mq137_level3,z0=mq138_level0,z1=mq138_level1,z2=mq138_level2,z3=mq138_level3,runtime1=intaketimes,runtime2=fittimes,runtime3=exhausttimes)
    return redirect(url_for('login'))

@app.route('/logout')
@app.route('/logout/')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@app.route('/register/', methods=['GET', 'POST'])
def register():
    msg = 'Creating User Account Page'
    # If already loggedin, redirect to home
    if 'loggedin' in session:
        return redirect(url_for('home'))
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        username_already_exist = User.check_username_exist(username)
        email_already_exist = User.check_email_exist(email)
        if username_already_exist:
            msg = '이미 등록된 사용자입니다.'
        elif email_already_exist:
            msg = '메일 주소가 이미 등록된 주소입니다.'
        else:
            User.useradd(username, password, email)
            msg = '사용자 등록이 완료되었습니다.'
            return redirect(url_for('login'))
    return render_template('register.html', msg=msg)

# get client's ip test
@app.route('/ip', methods=['GET'])
@app.route('/ip/', methods=['GET'])
def client_ip():
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

@app.route('/sensor_stop', methods=['POST','GET'])
@app.route('/sensor_stop/', methods=['POST','GET'])
def sensor_stop():
    # Check if user is loggedin
    if 'loggedin' in session:
        select_sensor = [0,1,2,3,4]
        msg1 = web_dbsave.action_config("runstop", select_sensor)
        msg = 'autorun stop flag set={0}'.format(msg1)
        app.logger.info(msg)
        flash(msg)
        return render_template('home.html', username=session['username'], logintime=session['logintime'], userip=session['userip'],msg=msg)
    return redirect(url_for('login'))
    
@app.route('/sensor_control', methods=['POST','GET'])
@app.route('/sensor_control/', methods=['POST','GET'])
def sensor_control():
    commmand_no = 0
    # Check if user is loggedin
    select_sensor = []
    if 'loggedin' in session:
        username=session['username']
        msg2 = "INOD .."
        if request.method == 'POST':
            if not request.form.get('no1') and not request.form.get('no2')  and not request.form.get('no3')  and not request.form.get('no4')  and not request.form.get('no5'):
                msg = 'Please Selected Sensor....'
                flash(msg)
                return render_template('home.html', msg=msg)
            if request.form.get('no1') or request.form.get('no2')  or request.form.get('no3')  or request.form.get('no4')  or request.form.get('no5'):
                if request.form.get('no1'):
                    select_sensor.append(int(request.form['no1']))
                if request.form.get('no2'):
                    select_sensor.append(int(request.form['no2']))
                if request.form.get('no3'):
                    select_sensor.append(int(request.form['no3']))
                if request.form.get('no4'):
                    select_sensor.append(int(request.form['no4']))
                if request.form.get('no5'):
                    select_sensor.append(int(request.form['no5']))

            runcount = int(request.form['repeat_value'])

            commmand_no = int(request.form['cmd_check'])
            cycle_time = int(request.form['cycle_time'])

            #명령어 제어 부분(.apply_async(args=[email_data], countdown=60))
            if commmand_no == 1:
                msg2 = web_dbsave.action_config("autorun", select_sensor, runcount, cycle_time)
            elif commmand_no == 2:
                msg2 = web_dbsave.action_config("sd_read", select_sensor)
            elif commmand_no == 3:
                msg2 = web_dbsave.action_config("exhaust", select_sensor)
            elif commmand_no == 4:
                msg2 = web_dbsave.action_config("intake", select_sensor)
            
        msg = 'Sensor comamnd action completed!![{0}]'.format(msg2)
        flash(msg)
        return render_template('home.html', username=session['username'], logintime=session['logintime'], userip=session['userip'],msg=msg)
    return redirect(url_for('login'))

@app.route('/pump_in_out_time_conf', methods=['GET', 'POST'])
@app.route('/pump_in_out_time_conf/', methods=['GET', 'POST'])
def pump_in_out_time_conf():
    select_sensor = []
    commmand_no = 0
    # Check if user is loggedin  request.args.get
    if 'loggedin' in session:
        if request.method == 'POST':
            if not request.form.get('no1') and not request.form.get('no2')  and not request.form.get('no3')  and not request.form.get('no4')  and not request.form.get('no5') and not request.form.get('cmd_check') and not request.form.get('running_time'):
                msg = 'Please Selected Sensor and  Mode and running time..'
                flash(msg)
                #return render_template('home.html', msg=msg)
                return redirect('home', msg=msg)
            if request.form.get('no1') or request.form.get('no2')  or request.form.get('no3')  or request.form.get('no4')  or request.form.get('no5'):
                if request.form.get('no1'):
                    select_sensor.append(int(request.form['no1']))
                if request.form.get('no2'):
                    sensor_ids = int(request.form['no2'])
                    select_sensor.append(int(request.form['no2']))
                if request.form.get('no3'):
                    select_sensor.append(int(request.form['no3']))
                if request.form.get('no4'):
                    select_sensor.append(int(request.form['no4']))
                if request.form.get('no5'):
                    select_sensor.append(int(request.form['no5']))
                    
                runningtimes = []
                runningtimes.append(int(request.form['running_time1']))
                runningtimes.append(int(request.form['running_time2']))
                runningtimes.append(int(request.form['running_time3']))
                
                web_dbsave.action_config("pumpruntime", select_sensor, runningtimes)
                msg = 'After 10 minutes, the {0} sensor pumping works.'.format(len(select_sensor))
                app.logger.info(msg)
                return redirect(url_for('home', msg=msg))
    return redirect(url_for('login'))
    
@app.route('/reset_sensor', methods=['GET', 'POST'])
@app.route('/reset_sensor/', methods=['GET', 'POST'])
def reset_sensor():
    select_sensor = []
    # Check if user is loggedin  request.args.get
    if 'loggedin' in session:
        username=session['username']
        if request.method == 'POST':
            if not request.form.get('no1') and not request.form.get('no2')  and not request.form.get('no3')  and not request.form.get('no4')  and not request.form.get('no5'):
                msg = 'Please Selected Sensor....'
                flash(msg)
                return render_template('home.html', msg=msg)
            if request.form.get('no1') or request.form.get('no2')  or request.form.get('no3')  or request.form.get('no4')  or request.form.get('no5'):
                if request.form.get('no1'):
                    select_sensor.append(int(request.form['no1']))
                if request.form.get('no2'):
                    sensor_ids = int(request.form['no2'])
                    select_sensor.append(int(request.form['no2']))
                if request.form.get('no3'):
                    select_sensor.append(int(request.form['no3']))
                if request.form.get('no4'):
                    select_sensor.append(int(request.form['no4']))
                if request.form.get('no5'):
                    select_sensor.append(int(request.form['no5']))
                # sesor_id
                web_dbsave.action_config("pumpreset", select_sensor)
                msg = 'After 10 minutes, the {0} sensor device works.'.format(len(select_sensor))
                app.logger.info(msg)
                return render_template('home.html', username=session['username'], logintime=session['logintime'], userip=session['userip'],msg=msg)
    return redirect(url_for('login'))
    
@app.route('/sensor_ro_control', methods=['GET', 'POST'])
@app.route('/sensor_ro_control/', methods=['GET', 'POST'])
def sensor_ro_control():
    select_sensor = []
    # Check if user is loggedin
    if 'loggedin' in session:
        username=session['username']
        if request.method == 'POST':
            if not request.form.get('no1') and not request.form.get('no2')  and not request.form.get('no3')  and not request.form.get('no4')  and not request.form.get('no5'):
                msg = 'Please Selected Sensor....'
                flash(msg)
                return render_template('home.html', msg=msg)
            if request.form.get('no1') or request.form.get('no2')  or request.form.get('no3')  or request.form.get('no4')  or request.form.get('no5'):
                if request.form.get('no1'):
                    select_sensor.append(int(request.form['no1']))
                if request.form.get('no2'):
                    select_sensor.append(int(request.form['no2']))
                if request.form.get('no3'):
                    select_sensor.append(int(request.form['no3']))
                if request.form.get('no4'):
                    select_sensor.append(int(request.form['no4']))
                if request.form.get('no5'):
                    select_sensor.append(int(request.form['no5']))

            ro1  = request.form['Mq135Value']
            ro2  = request.form['Mq136Value']
            ro3  = request.form['Mq137Value']
            ro4  = request.form['Mq138Value']
            # sesor_id, ro1, ro2, ro3, ro4
            msg1 = web_dbsave.config_ro_value(select_sensor,ro1, ro2, ro3, ro4)
            msg2 = web_dbsave.action_config("roconfig", select_sensor)
            msg = 'sensor ro calibration configuration completed[{0}, {1}]'.format(msg1, msg2)
            flash(msg)
        return render_template('home.html', username=session['username'], logintime=session['logintime'], userip=session['userip'],msg=msg)
    return redirect(url_for('login'))

@app.route('/sensor_scope_control', methods=['GET', 'POST'])
@app.route('/sensor_scope_control/', methods=['GET', 'POST'])
def sensor_scope_control():
    select_sensor = []
    # Check if user is loggedin
    if 'loggedin' in session:
        username=session['username']
        if request.method == 'POST':
            if not request.form.get('no1') and not request.form.get('no2')  and not request.form.get('no3')  and not request.form.get('no4')  and not request.form.get('no5'):
                msg = 'Please Selected Sensor....'
                flash(msg)
                return render_template('home.html', msg=msg)
            if request.form.get('no1') or request.form.get('no2')  or request.form.get('no3')  or request.form.get('no4')  or request.form.get('no5'):
                if request.form.get('no1'):
                    select_sensor.append(int(request.form['no1']))
                if request.form.get('no2'):
                    select_sensor.append(int(request.form['no2']))
                if request.form.get('no3'):
                    select_sensor.append(int(request.form['no3']))
                if request.form.get('no4'):
                    select_sensor.append(int(request.form['no4']))
                if request.form.get('no5'):
                    select_sensor.append(int(request.form['no5']))
                    
            scop0 = request.form['Mq135Value0'] + ';' + request.form['Mq135Value1'] + ';' + request.form['Mq135Value2'] + ';' + request.form['Mq135Value3']
            scop1 = request.form['Mq136Value0'] + ';' + request.form['Mq136Value1'] + ';' + request.form['Mq136Value2'] + ';' + request.form['Mq136Value3']
            scop2 = request.form['Mq137Value0'] + ';' + request.form['Mq137Value1'] + ';' + request.form['Mq137Value2'] + ';' + request.form['Mq137Value3']
            scop3 = request.form['Mq138Value0'] + ';' + request.form['Mq138Value1'] + ';' + request.form['Mq138Value2'] + ';' + request.form['Mq138Value3']
            #sensorid 1 ~ 2, MQ135 ~ 138, Level 0 ~ 3, x 절편, y절편, 기울기
            msg1 = web_dbsave.config_scope_value(select_sensor,scop0, scop1, scop2, scop3)
            msg2 = web_dbsave.action_config("scopeconfig", select_sensor)
            msg = 'sensor scope calibration configuration completed[{0},{1}]'.format(msg1, msg2)
            
        return render_template('home.html', username=session['username'], logintime=session['logintime'], userip=session['userip'],msg=msg)
    return redirect(url_for('login'))
    