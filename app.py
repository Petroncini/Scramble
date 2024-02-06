import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, flash, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///schedule.db")

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "GET":

        user_tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", session['user_id'])
        tasks = []

        for row in user_tasks:
            task = {}
            task['task_id'] = row['task_id']
            task['name'] = row['name']
            task['color'] = row['color']
            task['fixed'] = row['fixed']
            tasks.append(task)

        return render_template("home.html", tasks=tasks)

    if request.method == "POST":
        schedule = db.execute("SELECT * FROM schedule WHERE user_id = ?", session['user_id'])
        return jsonify(schedule)




@app.route("/login", methods = ["GET", "POST"])
def login():
    if  request.method == "GET":

        return render_template("login.html")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Username required")
            return redirect("/login")

        if not password:
            flash("Password required")
            return redirect("/login")

        users = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(users) == 0:
            flash("Account does not exist. Please register")
            return redirect("/login")


        if(check_password_hash(users[0]['hash'], password)):
            session['user_id'] = users[0]["id"]
            return redirect("/")
        else:
            flash("Incorrect password")
            return redirect("/login")



    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

        if not username:
            flash("Username required")
            return redirect("/register")

        if not password:
            flash("Password required")
            return redirect("/register")

        if not password_confirm:
            flash("Please confirm password")
            return redirect("/register")

        if password != password_confirm:
            flash("Password must match")
            return redirect("/register")

        users = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(users) != 0:
            flash("Username taken")
            redirect("/register")

        hash = generate_password_hash(password)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        new_user = db.execute("SELECT id FROM users WHERE username = ?", username)

        new_id = new_user[0]['id']
        values = ""
        for day in range(1, 8):
            for hour in range(0, 24):
                if day == 7 and hour == 23:
                    values += f"('{new_id}', '{day}', '{hour}');"
                else:
                    values += f"('{new_id}', '{day}', '{hour}'), "

        query = "INSERT INTO schedule (user_id, day, hour) VALUES " + values
        db.execute(query)
        flash("Registration succesfull")

        return redirect("/login")


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    if request.method == "GET":
        user_tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", session['user_id'])
        tasks = []
        
        for row in user_tasks:
            task = {}
            task['task_id'] = row['task_id']
            task['name'] = row['name']
            task['color'] = row['color']
            task['fixed'] = row['fixed']
            tasks.append(task)

        return render_template("tasks.html", tasks=tasks)

    if request.method == "POST":
        task_name = request.form.get("task_name")
        task_color = request.form.get("task_color")
        action = request.form.get("action")
        task_id = request.form.get("task_id")
        task_fixed = request.form.get("task_fixed")

        print("HEllOOOO")
        print(request.form)
        print(task_fixed)

        if not task_name:
            flash("Task name required")
            redirect("/tasks")

        if not task_color:
            flash("Task color required")
            redirect("/tasks")

        if not action:
            flash("How the h*** did you submit the form without pressing the button?")
            redirect("tasks")

        if action == "add":
            db.execute("INSERT INTO tasks (user_id, name, color, fixed) VALUES (?, ?, ?, ?)", session['user_id'], task_name, task_color, task_fixed)

        elif action == "edit":
            db.execute("UPDATE tasks SET name = ?, color = ?, fixed = ? WHERE task_id = ?", task_name, task_color, task_fixed, task_id)

        elif action == "delete":
            db.execute("DELETE FROM tasks WHERE task_id = ?", task_id)

        return redirect("/tasks")

@app.route("/get_tasks")
@login_required
def get_tasks():
    
    user_tasks = db.execute("SELECT * FROM tasks WHERE user_id = ?", session['user_id'])
    tasks = [{}, {}] # [0] name, [1] color

    for row in user_tasks:
        tasks[0][row['task_id']] = row['name']
        tasks[1][row['task_id']] = row['color']

    
    return jsonify(tasks)

@app.route("/get_schedule")
@login_required
def get_schedule():
    
    user_schedule = db.execute("SELECT * FROM schedule WHERE user_id = ?", session['user_id'])

    
    days, hours = 7, 24
    schedule = [[0 for x in range(days)] for y in range(hours)] 

    # print(schedule)
    cell = 0

    for day in range(0, 7):
        for hour in range(0, 24):
            # print(f"day: {day}, hour: {hour}, cell: {cell}")
            # print(f"Schedule| day: {user_schedule[cell]['day']}, hour: {user_schedule[cell]['hour']}")
            schedule[hour][day] = user_schedule[cell]['task_id']
            cell += 1

    return jsonify(schedule)

@app.route("/update_schedule", methods=["POST"])
@login_required
def update_schedule():
    print("hello")
    print(request.json)
    
    task_id = request.json.get("task_id")
    hour = request.json.get("hour")
    day = request.json.get("day")
    

    # print(f"UPDATE schedule SET task_id = {task_id} WHERE user_id = {session['user_id']} AMD hour = {hour} AND day = {day}")
    
    db.execute("UPDATE schedule SET task_id = ? WHERE user_id = ? AND hour = ? AND day = ?", task_id, session['user_id'], hour, day)
    return ["Ok"]

@app.route("/bulk_set", methods=["POST"])
@login_required
def bulk_set():
    print(request.form)
    start = request.form.get("start")
    end = request.form.get("end")
    task_id = request.form.get("task_id")

    if not task_id:
        flash("Task required")
        return redirect("/")

    if not start or not end or int(end) <= int(start):
        print("Incorrect time")
        flash("Incorrect time")
        return redirect("/")

    days = {}
    for i in range(1, 8):
        if request.form.get(f"day_{i}"):
            days[i] = 1
        else:
            days[i] = 0
        
    print(days)

    start = int(start)
    end = int(end)


    for day in range(1, 8):
        for hour in range(start, end + 1):
            if days[day] == 1:
                # print(f"Day: {day}, Hour: {hour}")
                # print(f"UPDATE schedule SET task_id = {task_id} WHERE user_id = {session['user_id']} AND day = {day} and hour = {hour}")
                db.execute("UPDATE schedule SET task_id = ? WHERE user_id = ? AND day = ? and hour = ?", task_id, session['user_id'], day, hour)
    

    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
