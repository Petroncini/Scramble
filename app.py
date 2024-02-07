import os
import io
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, flash, jsonify, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd
import matplotlib.pyplot as plt
import numpy as np

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

@app.route("/metrics")
@login_required
def metrics():
    if request.method == "GET":
        return render_template("metrics.html")
    

@app.route("/check_date_overlap", methods=["POST"])
@login_required
def check_date_overlap():
    day = int(request.json['day'])
    month = int(request.json['month'])
    year = int(request.json['year'])
    weekday = int(request.json['weekday'])

    if weekday != 6:
        return jsonify([1])

    

    date = datetime(year, month, day)

    # Get the ISO week number
    iso_week_number = date.isocalendar()[1] + 1

    weeks = db.execute("SELECT week FROM productivity WHERE user_id = ? AND year = ? AND week = ?", session['user_id'], year, iso_week_number)
    
    if len(weeks) != 0:
        return jsonify([2])

    return jsonify([0])

@app.route("/upload_week_data", methods=["POST"])
@login_required
def upload_week_data():
    sunday_date = request.form.get("sunday_date")
    overwrite = request.form.get("overwrite")

    if not overwrite:
        flash("Overwrite not enabled")
        return redirect("/metrics")

    date_object = datetime.strptime(sunday_date, "%Y-%m-%d")
    year = date_object.year
    week_number = date_object.isocalendar()[1] + 1

    current_schedule = db.execute("SELECT * FROM schedule WHERE user_id = ?", session['user_id'])
    user_tasks = db.execute("SELECT task_id, fixed FROM tasks WHERE user_id = ?", session['user_id'])

    fixed_tasks = {}

    for task in user_tasks:
        fixed_tasks[task['task_id']] = task['fixed']
    
    
    db.execute("DELETE FROM productivity WHERE user_id = ? AND year = ? AND week = ?", session['user_id'], year, week_number)

    values = ""

    for row in current_schedule:
        if row['task_id'] != None:
            if fixed_tasks[row['task_id']] == "not_fixed":
                values += f"('{session['user_id']}', '{year}', '{week_number}','{row['day']}', '{row['hour']}', '{row['task_id']}', '{row['progress']}'),"
                
    values = values[:-1] + ";"
    db.execute("INSERT INTO productivity (user_id, year, week, day, hour, task_id, progress) VALUES " + values)
    return redirect("/metrics")

@app.route("/visualize_week_overview", methods=["POST"])
@login_required
def visualize_week_overview():
    print("Request received")

    day = int(request.json['day'])
    month = int(request.json['month'])
    year = int(request.json['year'])
    task_id = int(request.json['task_id'])
    

    date = datetime(year, month, day)

    # Get the ISO week number
    week = date.isocalendar()[1] + 1

    print(f"Day: {day}, Month: {month}, Year: {year}, Week: {week}")

    if task_id == 0:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ?", session['user_id'], year, week)
    else:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? AND task_id = ", session['user_id'], year, week, task_id)
    

    weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    daily_sum = []
    for i in range(0, 7):
        daily_sum.append({})
        daily_sum[i]['not_started'] = 0
        daily_sum[i]['started'] = 0
        daily_sum[i]['done'] = 0
        daily_sum[i]['goal'] = 0

    
    for row in data:
        if row['progress'] == "not_started":
            daily_sum[row['day'] - 1]["not_started"] += 1

        elif row['progress'] == "started":
            daily_sum[row['day'] - 1]["started"] += 1

        elif row['progress'] == "done":
            daily_sum[row['day'] - 1]["done"] += 1

        daily_sum[row['day'] - 1]["goal"] += 1
        print(f"Day: {weekdays[row['day'] - 1]}, Goal: {daily_sum[row['day'] - 1]["goal"]}")

    for i in range(0, 7):
        print(f"______Day: {weekdays[i]}, Goal: {daily_sum[i]["goal"]}")
        daily_sum[i]['percentage_complete'] = daily_sum[i]['done'] / daily_sum[i]['goal']

    productivity_data = daily_sum
    for row in productivity_data:
        print(row)

    # Extracting labels and values for each day
    days = [f"{weekdays[i]}" for i in range(len(productivity_data))]
    started_values = [day['started'] for day in productivity_data]
    done_values = [day['done'] for day in productivity_data]
    goal_values = [day['goal'] for day in productivity_data]

    plt.figure().set_figwidth(10)
    plt.figure().set_figheight(10)

    # Set up the figure and axes
    fig, ax = plt.subplots()

    # Bar width
    bar_width = 0.25

    # Set the positions of bars on X-axis
    r1 = np.arange(len(days))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]

    # Plotting the bars
    plt.bar(r1, started_values, color='blue', width=bar_width, edgecolor='grey', label='Started')
    plt.bar(r2, done_values, color='green', width=bar_width, edgecolor='grey', label='Done')
    plt.bar(r3, goal_values, color='orange', width=bar_width, edgecolor='grey', label='Goal')

    # Adding labels
    plt.xlabel('Days', fontweight='bold', fontsize=15)
    plt.xticks([r + bar_width for r in range(len(days))], days)
    plt.xticks(rotation=20, ha='right')

    # Adding legend
    plt.legend()

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)

    # Clear the plot to avoid it being shown in the server
    plt.clf()

    return send_file(img_buf, mimetype='image/png')

@app.route("/check_for_week_overview", methods=["POST"])
@login_required
def check_for_week_overview():
    
    day = int(request.json['day'])
    month = int(request.json['month'])
    year = int(request.json['year'])
    weekday = int(request.json['weekday'])

    if weekday != 6:
        return jsonify([1]) # not a sunday

    

    date = datetime(year, month, day)

    # Get the ISO week number
    iso_week_number = date.isocalendar()[1] + 1

    weeks = db.execute("SELECT week FROM productivity WHERE user_id = ? AND year = ? AND week = ?", session['user_id'], year, iso_week_number)
    
    if len(weeks) == 0:
        return jsonify([2]) # week not on record

    return jsonify([0]) # checks out


@app.route("/check_for_day_overview", methods=["POST"])
@login_required
def check_for_day_overview():
    
    day = int(request.json['day'])
    month = int(request.json['month'])
    year = int(request.json['year'])
    weekday = int(request.json['weekday'])
    
    
    print(weekday)
    date = datetime(year, month, day)

    # Get the ISO week number
    iso_week_number = date.isocalendar()[1]

    if (weekday == 6):
        iso_week_number += 1
    

    print(iso_week_number)

    weeks = db.execute("SELECT week FROM productivity WHERE user_id = ? AND year = ? AND week = ?", session['user_id'], year, iso_week_number)
    print(weeks)

    if len(weeks) == 0:
        print("Day not on record")
        return jsonify([1]) # week not on record

    return jsonify([0]) # checks out


@app.route("/visualize_day_overview", methods=["POST"])
@login_required
def visualize_day_overview():
    print("Request received")

    day = int(request.json['day'])
    month = int(request.json['month'])
    year = int(request.json['year'])
    task_id = int(request.json['task_id'])
    weekday = int(request.json['weekday'])

    
    
    date = datetime(year, month, day)

    # Get the ISO week number
    week = date.isocalendar()[1]

    # we need to map datetime's weekday format to out own so
    # 0 -> 2, 1 -> 3, ... 6 
    if weekday == 6:
        weekday = 1
    else:
        weekday += 2

    if (weekday == 6):
        week += 1

    print(f"Day: {weekday}, Month: {month}, Year: {year}, Week: {week}")
    # The day column in the table is actually the weekday, my bad. So what we need to pass on to the query is the weekday + 1
    # :/

    if task_id == 0:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? AND day = ?", session['user_id'], year, week, weekday)
    else:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? AND day =? AND task_id = ", session['user_id'], year, week, weekday, task_id)
    
    
    hourly_progress = []
    total_progress = 0

    for i in range(0, 24):
        hourly_progress.append({})
        hourly_progress[i]['progress'] = 0
    
    last_hour_set = 0

    def fill_in(start, end, progress):
        for

    for row in data:
        if row['hour'] - last_hour_set > 1:
            fill_in(last_hour_set, row['hour'], total_progress)
        if row['progress'] == "started":
            total_progress += 1
            hourly_progress[row['hour']]['progress'] += total_progress
            
            print(row['hour'])
        elif row['progress'] == "done":
            total_progress += 2
            hourly_progress[row['hour']]['progress'] += total_progress
            print(row['hour'])
        else:
            hourly_progress[row['hour']]['progress'] = total_progress
    print(data)
    print(len(hourly_progress))
    hours = [f"{i}:00" for i in range(len(hourly_progress))]
    progress = [hour['progress'] for hour in hourly_progress]

    plt.figure().set_figwidth(15)
    plt.plot(hours, progress, color="blue")
    plt.xlabel("Hours")
    plt.ylabel("Progress")
    plt.xticks(rotation=45, ha='right')
    plt.title("Progress by hour")
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)

    # Clear the plot to avoid it being shown in the server
    plt.clf()

    return send_file(img_buf, mimetype='image/png')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
