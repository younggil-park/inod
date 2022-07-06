#-*- coding:utf-8 -*-
from flask_mysqldb import MySQL
import MySQLdb.cursors
from app001.web_app import app
import bcrypt

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'atek21.com'
app.config['MYSQL_DB'] = 'sensordb'
app.config['MYSQL_PORT'] = 3306

# Intialize MySQL
mysql = MySQL(app)

class User():
    def login_check(input_username, input_password):
        # bcrypt hash transfer
        input_password = input_password.encode('utf-8')
        # MySQL DB에 해당 계정 정보가 있는지 확인
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', [input_username])
        # 값이 유무 확인 결과값 account 변수로 넣기
        account = cursor.fetchone()
        if account != None:
            check_password = bcrypt.checkpw(input_password, account['password'].encode('utf-8'))
        else:
            account = "None"
            check_password = "None"
        return account, check_password
    def get_information(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', id)
        account = cursor.fetchone()
        return account
    def update_fromip(fromip, id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE `accounts` SET `fromip`=%s WHERE `id`=%s', (fromip, str(id)))
        mysql.connection.commit()
    def useradd(username, password, email):
        # bcrypt hash transfer
        password = (bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt())).decode('utf-8')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO `accounts` (`username`, `password`, `email`) VALUES (%s, %s, %s)", (username, password, email))
        mysql.connection.commit()
    def check_username_exist(username):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username, ))
        account = cursor.fetchone()
        return account
    def check_email_exist(email):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        account = cursor.fetchone()
        return account
