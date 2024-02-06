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

        db.execute("INSERT INTO tasks (user_id, name, color) VALUES (?, '___NULL___', '#000000')", new_user[0]['id'])

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
    tasks = [{}, {}, {}] # [0] name, [1] color

    for row in user_tasks:
        tasks[0][row['task_id']] = row['name']
        tasks[1][row['task_id']] = row['color']
        tasks[2][row['task_id']] = row['fixed']

    
    return jsonify(tasks)

@app.route("/get_schedule")
@login_required
def get_schedule():
    
    user_schedule = db.execute("SELECT * FROM schedule WHERE user_id = ?", session['user_id'])

    
    days, hours = 7, 24
    schedule = [[{'task_id': None, 'progress': "not_started"} for x in range(days)] for y in range(hours)] 

    # print(schedule)
    cell = 0

    for day in range(0, 7):
        for hour in range(0, 24):
            # print(f"day: {day}, hour: {hour}, cell: {cell}")
            # print(f"Schedule| day: {user_schedule[cell]['day']}, hour: {user_schedule[cell]['hour']}")
            schedule[hour][day]['task_id'] = user_schedule[cell]['task_id']
            schedule[hour][day]['progress'] = user_schedule[cell]['progress']
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
    print(task_id)

    task = db.execute("SELECT fixed FROM tasks WHERE task_id = ?", task_id)
    task_fixed = task[0]['fixed']
    print(task_fixed)

    # print(f"UPDATE schedule SET task_id = {task_id} WHERE user_id = {session['user_id']} AMD hour = {hour} AND day = {day}")
    if task_fixed == "fixed":
        db.execute("UPDATE schedule SET task_id = ?, progress = 'done' WHERE user_id = ? AND hour = ? AND day = ?", task_id, session['user_id'], hour, day)
    
    else:
        db.execute("UPDATE schedule SET task_id = ?, progress = 'not_started' WHERE user_id = ? AND hour = ? AND day = ?", task_id, session['user_id'], hour, day)

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

    if not start or not end or int(end) < int(start):
        print("Incorrect time")
        flash("Incorrect time")
        return redirect("/")
    
    task = db.execute("SELECT fixed FROM tasks WHERE task_id = ?", task_id)
    task_fixed = task[0]['fixed']

    days = {}
    for i in range(1, 8):
        if request.form.get(f"day_{i}"):
            days[i] = 1
        else:
            days[i] = 0
        
    print(days)

    start = int(start)
    end = int(end)

    if task_fixed == "not_fixed":
        for day in range(1, 8):
            if start != end:
                for hour in range(start, end + 1):
                    if days[day] == 1:
                        # print(f"Day: {day}, Hour: {hour}")
                        # print(f"UPDATE schedule SET task_id = {task_id} WHERE user_id = {session['user_id']} AND day = {day} and hour = {hour}")
                        db.execute("UPDATE schedule SET task_id = ? WHERE user_id = ? AND day = ? and hour = ?", task_id, session['user_id'], day, hour)
            else:

                db.execute("UPDATE schedule SET task_id = ? WHERE user_id = ? AND day = ? and hour = ?", task_id, session['user_id'], day, start)
    else:
        for day in range(1, 8):
            if start != end:
                for hour in range(start, end + 1):
                    if days[day] == 1:
                        # print(f"Day: {day}, Hour: {hour}")
                        # print(f"UPDATE schedule SET task_id = {task_id} WHERE user_id = {session['user_id']} AND day = {day} and hour = {hour}")
                        db.execute("UPDATE schedule SET task_id = ?, progress = 'done' WHERE user_id = ? AND day = ? and hour = ?", task_id, session['user_id'], day, hour)
            else:

                db.execute("UPDATE schedule SET task_id = ?, progress = 'done' WHERE user_id = ? AND day = ? and hour = ?", task_id, session['user_id'], day, start)


    return redirect("/")

@app.route("/update_progress", methods=["POST"])
@login_required
def update_progress():
    hour = request.form.get("hour")
    day = request.form.get("day")
    radio_name = request.form.get("radio_name")
    progress = request.form.get(radio_name)

    print(f"Hour: {hour}, day: {day}, radio_name: {radio_name}, progress: {progress}")

    db.execute("UPDATE schedule SET progress = ? WHERE user_id = ? AND hour = ? AND day = ?", progress, session['user_id'], hour, day)

    return '', 204

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
