from flask import Flask, render_template, request, redirect, url_for, jsonify
from jinja2 import Environment
from flask_socketio import SocketIO
from cryptography.fernet import Fernet
import db
from datetime import time
from db_oop import student_account, classes, getAllClasses, insertToTaken, deleteFromTaken, getTakenCourses, insertToSchedules, deleteFromSchedule, getSchedule
import search, json, bcrypt
import psycopg2
from recommend import remainingHours, remainingCourses, recommendCourses

'''This is where flask application is being made.'''
app = Flask(__name__, template_folder="templates")
salt =  b'$2b$12$Hw.Vq/gUQ1/0s37Wep3xP.'


connection = psycopg2.connect(
    dbname='NewDB',
    user='postgres',
    password='123456',
    host='localhost',
    port='5432'
)

# Directs to Main Page 
@app.route("/", methods = ['GET', 'POST'])
def login():
    return render_template("login.html")

@app.route("/signup", methods = ['GET', 'POST'])
def signup():
    return render_template("signup.html")      

@app.route("/home/<username>/<major>", methods = ['GET', 'POST'])
def home(username, major):
    return render_template("welcome.html", name=username, major=major)   

@app.route("/courses", methods=['GET'])
def get_courses():
    classJSON = getAllClasses()
    # print(classJSON)
    return classJSON

@app.route("/course_display", methods=['GET'])
def show_classes():
    return render_template("course_display.html")   

@app.route("/search_course", methods = ["POST"])
def search_course():
    sQuery = request.form.get('query')
    courses = search.search(sQuery)

    # Convert the courses and sections to a list of dictionaries
    result = []
    for course in courses:
        sections = [{"crn": section.crn, 
                     "snum": section.snum, 
                     "days": section.days, 
                     "starttime": section.starttime,
                     "endtime": section.endtime, 
                     "campus": section.campus, 
                     "online": section.online, 
                     "building": section.building,
                     "room": section.room, 
                     "instructors": section.instructors}
                     for section in course.sections]
        
        instructors_list = [instructor for section in sections for instructor in section["instructors"]]
        
        course_dict = {
            "sid": course.sid,
            "cid": course.cid,
            "title": course.title,
            "description": course.description,
            "hours": course.hours,
            "sections": sections,
            "instructors": instructors_list,
        }

        result.append(course_dict)

    return json.dumps(result)  # Return the data as JSON

@app.route("/view_profile", methods = ["POST", "GET"])
def view_profile():
    if request.method =="POST":
        usrname = request.form.get('name')
        mjr = request.form.get('major')
    elif request.method == "GET":
        usrname = request.args.get('name')
        mjr = request.args.get('major')
    return render_template("profile.html", name=usrname, major=mjr)

@app.route("/guest_major", methods = ['GET', 'POST'])
def guest_major():
    return render_template("major.html", guest=True)    

@app.route("/redirect_major", methods = ['GET', 'POST'])
def redirect_major():
    name_input = request.form.get("name")
    password_input = request.form.get("pass")
    cursor = connection.cursor()
    query = "SELECT 1 FROM accounts WHERE (username = '"
    cursor.execute(query + name_input + "')")
    if(not cursor.fetchone()):
        print("AAADASESRAFUYDIUSADHGBIA: (" + name_input, password_input + ")")
        if(not (" " in name_input) and name_input != ""):
            if(not (" " in password_input) and password_input != ""):
                return render_template("major.html", name = name_input, password = password_input, guest=False)
            else:
                message = "Password Must Not Be Empty or Contain Spaces"
                return render_template("signup.html", message = message)
        else:
            message = "Username Must Not Be Empty or Contain Spaces"
            return render_template("signup.html", message = message)
    message = "Username Already Exists Please Try Another"
    return render_template("signup.html", message = message)

@app.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    account = student_account(username, bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8'))
    if account.isInDB():
        return jsonify(status="success")
    else:
        return jsonify(status="fail")

@app.route('/change_account_info', methods = ['GET'])
def change_account_info():
    username = request.args.get('username')
    major = request.args.get('major')
    print(username,  major)
    user = student_account(un=username, mjr=major).getFromDBWOPassword()
    print(user.username,user.major,user.password)
    return render_template('change_account_info.html', username=user.username, password=user.password, major=user.major)


@app.route('/update_account_info', methods=['POST'])
def update_account_info():
    # Extract data from the form
    old_username = request.form.get('old_username')
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    new_major = request.form.get('new_major')
    # Check if passwords match
    if new_password != confirm_password:
        return "Passwords do not match! Please go back and try again."
    # Use the changeInfo method from db_oop.py
    account = student_account(un=old_username).getFromDBWOPassword()
    print(account.username,account.major,account.password)
    if new_password != "":
        account.changeInfo(old_username, new_username, bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8'), new_major)
    else:
        account.changeInfo(old_username, new_username, new_password, new_major)
    return redirect(f'/view_profile?name={new_username}&major={new_major}')

# This version of the /result route uses the object-oriented approach for the database entries (see db_test.py)
# Still a work in progress.
@app.route("/result", methods = ['POST', 'GET'])
def result():
    source = request.form.get('source')

    if source == "major":                              # Handles signing up
        name_input = request.form.get("name")          # Extracts the "name" field from the form
        print("name is", name_input)
        password_input = request.form.get("pass")  # Extracts the "name" field from the dictionary
        major_input = request.form.get("major")
        isGuest = request.form.get('guest')
        newUser = student_account(un=name_input, pswd=bcrypt.hashpw(password_input.encode('utf-8'), salt).decode('utf-8'), mjr=major_input) 
        print(newUser.username)
        print(newUser.password)
        print(newUser.major)
        print(type(isGuest))
        if isGuest != "True":    # if not guest, then add account to database
            newUser.insertToDB()
            return render_template("login.html", done=True)
        else:                   # if guest, then send straight to welcome page without adding to database
            return redirect(url_for('home', username="Guest", major=newUser.major))
    
    elif source == "login":     # handles logging in
        name_input = request.form.get("name") 
        password_input = request.form.get("pass")
        guest_input = request.form.get("guest-input") 
        print("name is ", name_input)
        userInput = student_account(name_input, bcrypt.hashpw(password_input.encode('utf-8'), salt).decode('utf-8'))
        print(userInput.isInDB())
        if userInput.isInDB() is False:
            message = "Invalid Credentials"
            return render_template("login.html", message = message)
        else:
            student_db_info = userInput.getFromDB()
            return redirect(url_for("home", username=student_db_info.username, 
                                          major=student_db_info.major)) # renders and executes index.html again,
                                                                        # but this time with the given name
        
@app.route("/add_taken_course", methods = ['POST'])
def add_taken():
    data = request.json
    username = data.get('username')
    sid = data.get('sid')
    cid = data.get('cid')
    inserted = insertToTaken(username, sid, cid)
    print("added to taken")
    if inserted:
        return jsonify(status="success")
    else:
        return jsonify(status="fail")

@app.route("/del_taken_course", methods = ['POST'])
def del_taken():
    data = request.json
    username = data.get('username')
    sid = data.get('sid')
    cid = data.get('cid')
    deleted, message = deleteFromTaken(username, sid, cid)
    
    if deleted:
        print(message)
        return jsonify(status="success")
    else:
        print(message)
        return jsonify(status="fail")

@app.route("/get_taken_course/<username>", methods = ['POST', 'GET'])
def get_taken(username):
    taken_courses = getTakenCourses(username)
    courses_json = []
    for c in taken_courses:
        for id in c:
            courses_json.append({"sid": id[0], "cid" : id[1]})
    print("sent ", courses_json)
    return jsonify(courses_json)

@app.route("/get_remaining_courses/<username>", methods = ['GET'])
def get_remaining_courses(username):
    return jsonify(remainingCourses(username))

@app.route("/get_remaining_hours/<username>", methods = ['GET'])
def get_remaining_hours(username):
    return jsonify(remainingHours(username))

@app.route("/get_recommended_courses/<username>", methods = ['GET'])
def recommend(username):
    return jsonify(recommendCourses(username))

@app.route('/modify_schedule', methods = ['POST', 'DELETE'])
def modify_schedule():
    data = request.json
    user = data.get('username')
    crn = data.get('crn')
    schedule = data.get('sindex')

    if request.method =="POST":
        if insertToSchedules(user, crn, schedule):
            return 'success'
        else:
            return 'fail'
    elif request.method =="DELETE": 
        if deleteFromSchedule(user, crn, schedule):
            return 'success'
        else:
            return 'fail'

@app.route("/schedule_info", methods = ['POST'])
def schedule_info():
    data = request.json
    user = data.get('username')
    schedule = data.get('sindex')

    results = getSchedule(user, schedule)

    classes = []
    # Convert to proper format
    for result in results:
        if result[3] == None or result[4] == None:
            classInfo = {
                'crn': result[0],
                'sid': result[1],
                'cid': result[2],
                'starttime': None,
                'endtime': None,
                'days': []
            }
        else:
            classInfo = {
                'crn': result[0],
                'sid': result[1],
                'cid': result[2],
                'starttime': result[3].strftime('%H:%M') + ':00',
                'endtime': result[4].strftime('%H:%M') + ':00',
                'days': result[5]
            }

        classes.append(classInfo)

    print('Json', (classes))
    return jsonify(classes)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')