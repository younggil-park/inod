def check_activedb(sensorid):
  checkflage = ("runflage","sdreadflage","pumpflage","resetflage","roflage","scopeflage")
  sql = "SELECT * FROM sensoractionconfig WHERE sensorid = {0}".format(sensorid)
  db.execte(sql)
  flagedata = curs.fetchall()
  for i in flagedata:
    if checkflag[i] == i:
      sendaction(checkflage[i])

def runsendaction(sensorid):
  sql = "SELECT a.flage FROM tickettb a INNER JOIN actiontb b ON WHERE a.tickets = b.tickets and a.sensorid = {0}".format(sensorid)
  curs.execute(sql)
  rows = curs.fetchall()
  import mysql.connector  
  
  #Create the connection object   
  myconn = mysql.connector.connect(host = "localhost", user = "root",passwd = "google",database = "PythonDB")  
  
  #creating the cursor object  
  cur = myconn.cursor()  
  try:
    #joining the two tables on departments_id  
    cur.execute("select Employee.id, Employee.name, Employee.salary, Departments.Dept_id, Departments.Dept_Name from Departments join Employee on Departments.Dept_id = Employee.Dept_id")    
    for row in cur:  
        print("%d    %s    %d    %d    %s"%(row[0], row[1],row[2],row[3],row[4]))  
          
  except:  
    myconn.rollback()  
  
  myconn.close()
