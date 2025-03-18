import sqlite3
from flask import Flask,request
from flask_restful import Api,Resource
import json 
import os
from colorama import Fore, Back, Style
from gps_processor import *
app = Flask(__name__)
api = Api(app)

class ServerManager():
    def __init__(self, BASE_IP="127.0.0.1",sql_path="main.db"):
        self.BASE_IP = BASE_IP
        self.sql_path = sql_path
        self.con = sqlite3.connect(self.sql_path,check_same_thread=False)
        self.curs = self.con.cursor()
        self.sql_init()
        print("SCCS")
        
    def sql_init(self) -> None:
        self.curs.execute('''CREATE TABLE IF NOT EXISTS users_data(email STR NOT NULL,
                  password STR NOT NULL,
                  username STR NOT NULL)''')
        self.con.commit()
        self.curs.execute("""CREATE TABLE IF NOT EXISTS trail_data(trail_id INTEGER PRIMARY KEY NOT NULL, 
                trail_name STR NOT NULL,
                email STR,
                description STR,
                distance FLOAT,
                start_date STR,
                start_lat FLOAT,
                start_lon FLOAT,
                FOREIGN KEY (email) REFERENCES users_data (email))""")
        self.con.commit()
    
    def add_trail_table(self,trail_id):
        self.curs.execute(f'''CREATE TABLE IF NOT EXISTS leaderboard_{trail_id}(username STR NOT NULL,
                run_time int NOT NULL)''')
        self.con.commit()
        
        
    def add_trail(self,distance,date,start_lat,start_lon,trail_name,email,description) -> bool:
        self.curs.execute("SELECT email,trail_name FROM trail_data")
        for data in self.curs.fetchall():
            if str(data[0]) == email:
                if str(data[1]) == trail_name:
                    return False
        self.curs.execute('SELECT email FROM users_data')
        if email in [i[0] for i in self.curs.fetchall()]:
            self.curs.execute("INSERT INTO trail_data(trail_name,email,distance,start_date,start_lat,start_lon,description) VALUES (?,?,?,?,?,?,?)", (trail_name,email,float(distance),str(date),float(start_lat),float(start_lon),description))
            self.con.commit()
            self.curs.execute(f"""SELECT trail_id FROM trail_data WHERE email = "{email}" AND trail_name = "{trail_name}" """)
            self.add_trail_table(self.curs.fetchall()[0][0])
            return True
        else:         
            return False 
        
    def login(self,email,password) -> bool:
        self.curs.execute('SELECT email,password FROM users_data')
        for i in self.curs.fetchall():
            if str(i[0]) == email:
                if str(i[1]) == str(password):
                    return True
                else:
                    return False
        return False
    
    def sign_up(self,email,password,username) -> str:
        self.curs.execute('SELECT email,username FROM users_data')
        for i in self.curs.fetchall():
            if str(i[0]) == email:
                return "used_email"
            if str(i[1]) == username:
                return "used_username"
        self.curs.execute("""INSERT INTO users_data(email,password,username) VALUES (?,?,?)""", (email,password,username))
        self.con.commit()
        return "success"
    
    def add_rerun(self,email,name,run_time):
        run_time = int(run_time)
        self.curs.execute(f"""SELECT username FROM users_data WHERE email = "{email}" """)
        usernmae = self.curs.fetchall()[0][0]
        self.curs.execute(f"""SELECT trail_id FROM trail_data WHERE email = "{email}" AND trail_name = "{name}" """)
        id = self.curs.fetchall()[0][0]
        self.curs.execute(f"""SELECT run_time FROM leaderboard_{id} WHERE email = "{email}" """)
        prev_time = self.curs.fetchall()
        if self.curs.fetchall() == []:
            self.curs.execute(f"""INSERT INTO leaderboard_{id}(usernmae,run_time) VALUES (?,?)""",(usernmae,run_time))
            self.con.commit()
        else:
            prev_time = prev_time[0][0]
            if prev_time > run_time:
                self.curs.execute(f"""DELETE FROM leaderboard_{id} WHERE email = "{email}" """)
                self.curs.execute(f"""INSERT INTO leaderboard_{id}(usernmae,run_time) VALUES (?,?)""",(usernmae,run_time))
                self.con.commit()
        

    def get_all_trails(self,sort_type,location,page):
        trails_per_page = 1
        self.curs.execute('SELECT trail_name,email,distance,start_date,start_lat,start_lon,trail_id,description FROM trail_data')
        trail_list = self.curs.fetchall()
        main_tail_list = []
        for i in range(len(trail_list)):
            trail_list[i] = list(trail_list[i])
            self.curs.execute(f'SELECT username FROM users_data WHERE email = "{trail_list[i][1]}"')
            trail_list[i][1] = self.curs.fetchall()[0][0]
        
        if page * trails_per_page > (len(trail_list)):
            return trail_list
        if page != 0:
            print("a")
            if (len(trail_list) - 1) % (page * trails_per_page) != 0:
                return trail_list
            else:
                return trail_list[:(page + 1) * trails_per_page]
        else:
            return trail_list[:(page + 1    ) * trails_per_page]
        
    def get_leaderboard(self,trail_id,page):
        trails_per_page = 1
        self.curs.execute(f'SELECT usernmae, run_time FROM leaderboard_{trail_id} ORDER BY run_time')
        user_list = self.curs.fetchall()
        main_tail_list = []
        for i in range(len(user_list)):
            user_list[i] = list(user_list[i])
        
        if page * trails_per_page > (len(user_list)):
            return user_list
        if page != 0:
            print("a")
            if (len(user_list) - 1) % (page * trails_per_page) != 0:
                return user_list
            else:
                return user_list[:(page + 1) * trails_per_page]
        else:
            return user_list[:(page + 1) * trails_per_page]
            
    def check_rerun(self,email,trail_name):
        with open(f'{os.getcwd()}/saved_trails/{trail_name}_{email}.json',"r") as file:
            trail_json = json.load(file)
        with open(f"{os.getcwd()}/public_trail.json"):
            rerun_json= json.load(file)
        data = process_trail_validation(trail_json,rerun_json)[0]
        if data  == True:
           self.add_rerun(email,trail_json["name"],data[1])
           
        else:
            return False
        
        
MainManager = ServerManager()

@app.route('/add_trail/<trail_name>/<distance>/<date>/<start_lat>/<start_lon>/<description>/<email>/<password>',methods=['GET', 'POST'])
def post_add_trail(trail_name,distance,date,start_lat,start_lon,description,email,password) -> str:
    global MainManager
    if request.method == 'POST':
        if MainManager.login(email,password):
            json_file = request.files["file"]
            
            if MainManager.add_trail(distance,date,start_lat,start_lon,trail_name,email,description) == True:
                json_file.save(f'{os.getcwd()}/saved_trails/{trail_name}_{email}.json')
                return "True"
        return "False"
        
@app.route('/login/<email>/<password>')
def post_login(email,password):
    return str(MainManager.login(email,password))
    
@app.route('/sign_up/<email>/<password>/<username>')
def post_sign_up(email,password,username):
    global MainManager
    return MainManager.sign_up(email,password,username)

@app.route("/get_all_trails/<sort_type>/<location>/<page>")
def get_get_all_trails(sort_type,location,page):
    page = int(page)
    return {"data" : MainManager.get_all_trails(sort_type,location,page)}

@app.route("/load_rerun/<email>/<password>/trail_id")
def post_load_rerun(email,password,trail_id):
    global MainManager
    if request.method == 'POST':
        if MainManager.login(email,password):
            os.remove(f"{os.getcwd()}/public_trail.json")
            public_trail = request.files["file"]
            public_trail.save(f"{os.getcwd()}/public_trail.json")
            MainManager.check_rerun(email,trail_id)

@app.route("/get_leaderboard/<trail_id>")
def get_leaderboard(trail_id):
    global MainManager
    try:
        leaderboard = MainManager.get_leaderboard(trail_id)
    except:
        leaderboard = []
    return {"data" : leaderboard}


MainManager.sign_up("test","test","test")


app.run(host=MainManager.BASE_IP,debug=True)
