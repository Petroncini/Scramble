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
import logging
from dateutil.parser import parse

logging.getLogger('matplotlib.font_manager').disabled = True
pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)

# Configure application
app = Flask(__name__)


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
#db = SQL("sqlite:///schedule.db")
db = SQL("postgresql://scramble_db_user:NIhnBoM5P7INOwWuGoA0Lp0PcyGW67Qi@dpg-cn2ick7109ks73974sbg-a/scramble_db")

def days_elapsed(start_date, end_date):
    # Calculate the timedelta between the two datetime objects
    delta = datetime(end_date) - datetime(start_date)

    # Access the days attribute of the timedelta object
    days = delta.days

    return days

def generate_datetime(year, iso_week, iso_weekday):
    # Create a string in the format 'YYYY-Www-D', where 'w' is the week number and 'D' is the day of the week
    iso_date_string = f'{year}-W{iso_week}-{iso_weekday}'

    # Parse the ISO week date string and convert it to a datetime object
    dt_object = parse(iso_date_string)

    return dt_object

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
    
    user_schedule = db.execute("SELECT * FROM schedule WHERE user_id = ? ORDER BY day, hour", session['user_id'])

    

    days, hours = 7, 24
    schedule = [[{'task_id': None, 'progress': "not_started"} for x in range(days)] for y in range(hours)] 

 
    cell = 0 # something wrong here

    for day in range(0, 7):
        for hour in range(0, 24):
  
            schedule[hour][day]['task_id'] = user_schedule[cell]['task_id']
            schedule[hour][day]['progress'] = user_schedule[cell]['progress']
            cell += 1

    return jsonify(schedule)

@app.route("/update_schedule", methods=["POST"])
@login_required
def update_schedule():
   
    
    task_id = request.json.get("task_id")
    hour = request.json.get("hour")
    day = request.json.get("day")
  

    task = db.execute("SELECT fixed FROM tasks WHERE task_id = ?", task_id)
    task_fixed = task[0]['fixed']
    

   
    if task_fixed == "fixed":
        db.execute("UPDATE schedule SET task_id = ?, progress = 'done' WHERE user_id = ? AND hour = ? AND day = ?", task_id, session['user_id'], hour, day)
        
    
    else:
        db.execute("UPDATE schedule SET task_id = ?, progress = 'not_started' WHERE user_id = ? AND hour = ? AND day = ?", task_id, session['user_id'], hour, day)
        

    return ["Ok"]

@app.route("/bulk_set", methods=["POST"])
@login_required
def bulk_set():
  
    start = request.form.get("start")
    end = request.form.get("end")
    task_id = request.form.get("task_id")


    if not task_id:
        flash("Task required")
        return redirect("/")

    if not start or not end or int(end) < int(start):

        flash("Incorrect time")
        return redirect("/")
    
    task = db.execute("SELECT fixed FROM tasks WHERE task_id = %s", task_id)
    task_fixed = task[0]['fixed']

    days = {}
    for i in range(1, 8):
        if request.form.get(f"day_{i}"):
            days[i] = 1
        else:
            days[i] = 0
        
  

    start = int(start)
    end = int(end)

    if task_fixed == "not_fixed":
        progress = 'not_started'
    else:
        progress = 'done'

    
    if start != end: # more than one hour block
        db.execute(
            "UPDATE schedule SET task_id = %s, progress = %s WHERE user_id = %s AND day IN (1, 2, 3, 4, 5, 6, 7) AND hour BETWEEN %s AND %s",
            task_id, progress, session['user_id'], start, end
        )
        
    else:
        db.execute(
            "UPDATE schedule SET task_id = %s, progress = %s WHERE user_id = %s AND day IN (1, 2, 3, 4, 5, 6, 7) AND hour = %s",
            task_id, progress, session['user_id'], start
            )
            
    
            


    return redirect("/")

@app.route("/update_progress", methods=["POST"])
@login_required
def update_progress():
    hour = request.form.get("hour")
    day = request.form.get("day")
    radio_name = request.form.get("radio_name")
    progress = request.form.get(radio_name)

    

    db.execute("UPDATE schedule SET progress = ? WHERE user_id = ? AND hour = ? AND day = ? ", progress, session['user_id'], hour, day)

    return '', 204

@app.route("/metrics")
@login_required
def metrics():
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

        return render_template("metrics.html", tasks=tasks)
    

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

    weeks = db.execute("SELECT week FROM productivity WHERE user_id = ? AND year = ? AND week = ? ORDER BY day, hour", session['user_id'], year, iso_week_number)
    
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

    current_schedule = db.execute("SELECT * FROM schedule WHERE user_id = ? ORDER BY day, hour", session['user_id'])
    user_tasks = db.execute("SELECT task_id, fixed FROM tasks WHERE user_id = ? ", session['user_id'])

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
    

    day = int(request.json['day'])
    month = int(request.json['month'])
    year = int(request.json['year'])
    task_id = int(request.json['task_id'])
    
    

    date = datetime(year, month, day)

    # Get the ISO week number
    week = date.isocalendar()[1] + 1

   

    if task_id == 0:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? ORDER BY day, hour", session['user_id'], year, week)
    else:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? AND task_id = ? ORDER BY day, hour", session['user_id'], year, week, task_id)
    

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
        
   
    for i in range(0, 7): #goal might actually be zero
        if daily_sum[i]['goal'] != 0:
            daily_sum[i]['percentage_complete'] = daily_sum[i]['done'] / daily_sum[i]['goal']
        else:
            daily_sum[i]['percentage_complete'] = 1

    productivity_data = daily_sum
    

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

    weeks = db.execute("SELECT week FROM productivity WHERE user_id = ? AND year = ? AND week = ? ORDER BY day, hour", session['user_id'], year, iso_week_number)
    
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
    
    
    
    date = datetime(year, month, day)

    # Get the ISO week number
    iso_week_number = date.isocalendar()[1]

    if (weekday == 6):
        iso_week_number += 1
    

    

    weeks = db.execute("SELECT week FROM productivity WHERE user_id = ? AND year = ? AND week = ? ORDER BY day, hour", session['user_id'], year, iso_week_number)
    

    if len(weeks) == 0:
        return jsonify([2]) # week not on record

    return jsonify([0]) # checks out


@app.route("/visualize_day_overview", methods=["POST"])
@login_required
def visualize_day_overview():
    

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
    if (weekday == 6):
        week += 1


    if weekday == 6:
        weekday = 1
    else:
        weekday += 2

   
    
    # The day column in the table is actually the weekday, my bad. So what we need to pass on to the query is the weekday + 1
    # :/
    

    if task_id == 0:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? AND day = ? ORDER BY day, hour", session['user_id'], year, week, weekday)
    else:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND year = ? AND week = ? AND day =? AND task_id = ? ORDER BY day, hour", session['user_id'], year, week, weekday, task_id)
    
    
    
    hourly_progress = []
    total_progress = 0

    for i in range(0, 24):
        hourly_progress.append({})
        hourly_progress[i]['progress'] = 0
    
    last_hour_set = 0

    #maybe add the option to do cumulative or hour by hour

    def fill_in(start, end, progress):
        for i in range(start, end):
            hourly_progress[i]['progress'] = progress

    for row in data:
        if row['hour'] - last_hour_set > 1:
            fill_in(last_hour_set, row['hour'], total_progress)

        if row['progress'] == "started":
            total_progress += 1
            hourly_progress[row['hour']]['progress'] += total_progress
            
            
            
        elif row['progress'] == "done":
            total_progress += 2
            hourly_progress[row['hour']]['progress'] += total_progress
            
        else:
            hourly_progress[row['hour']]['progress'] = total_progress
        last_hour_set = row['hour']

   

    if data[len(data) - 1]['hour'] != 23:
        fill_in(last_hour_set, 24, total_progress)

    
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

@app.route("/visualize_history_overview", methods=["POST"])
@login_required
def visualize_history_overview():
    
    
    task_id = int(request.json['task_id'])
   
    

    if task_id == 0:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? ORDER BY day, hour", session['user_id'])
    else:
        data = db.execute("SELECT * FROM productivity WHERE user_id = ? AND task_id = ? ORDER BY day, hour", session['user_id'], task_id)
    
    #we need to count the number of days
    prev_year = data[0]['year']
    prev_week = data[0]['week']
    prev_day = data[0]['day']

    day_num = 1

    for row in data: # somethign wrong here

        
        if row['year'] != prev_year or row['week'] != prev_week or row['day'] != prev_day:
            
            prev_datetime = datetime.fromisocalendar(prev_year, prev_week, prev_day)
           

            prev_year = row['year']
            prev_week = row['week']
            prev_day = row['day']

            new_datetime =  datetime.fromisocalendar(prev_year, prev_week, prev_day)
            
            
            time_delta = new_datetime - prev_datetime
            days_difference = time_delta.days
            # Parse the ISO week date string and convert it to a datetime object
           
            day_num += days_difference


  
    daily_sum = []

    for i in range(0, day_num):
        daily_sum.append({})
        daily_sum[i]['not_started'] = 0
        daily_sum[i]['started'] = 0
        daily_sum[i]['done'] = 0
        daily_sum[i]['goal'] = 0

    row_index = 0
    prev_year = data[0]['year']
    prev_week = data[0]['week']
    prev_day = data[0]['day']

    
    for row in data:
        if row['year'] != prev_year or row['week'] != prev_week or row['day'] != prev_day:
            row_index += 1
            prev_year = row['year']
            prev_week = row['week']
            prev_day = row['day']
       
        if row['progress'] == "not_started":
            daily_sum[row_index]["not_started"] += 1

        elif row['progress'] == "started":
            daily_sum[row_index]["started"] += 1

        elif row['progress'] == "done":
            daily_sum[row_index]["done"] += 1

     
        daily_sum[row_index]["goal"] += 1
        



         # row day is not a useful index becaue it repeats

    for i in range(0, day_num):
        
        if daily_sum[i]['goal'] != 0:
            daily_sum[i]['percentage_complete'] = daily_sum[i]['done'] / daily_sum[i]['goal']
        else:
            
            daily_sum[i]['percentage_complete'] = -1
        

    productivity_data = daily_sum

    # Extracting labels and values for each day
    days = [f"{i}" for i in range(1, len(productivity_data) + 1)]
    started_values = [day['started'] for day in productivity_data]
    done_values = [day['done'] for day in productivity_data]
    goal_values = [day['goal'] for day in productivity_data]
    percentage_complete = [day['percentage_complete'] for day in productivity_data]

    plt.figure().set_figwidth(30)
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
    # plt.bar(r1, started_values, color='blue', width=bar_width, edgecolor='grey', label='Started')
    # plt.bar(r2, done_values, color='green', width=bar_width, edgecolor='grey', label='Done')
    # plt.bar(r3, goal_values, color='orange', width=bar_width, edgecolor='grey', label='Goal')
    plt.figure().set_figheight(10)
    plt.figure().set_figwidth(20)
    

    plt.plot(days, percentage_complete, color="green")

    # Adding labels
    plt.xlabel('Days', fontweight='bold', fontsize=15)
    plt.xticks([r + bar_width for r in range(len(days))], days)
    plt.xticks(rotation=20, ha='right')
    plt.title("Percentage complete by day")

    # Adding legend
    plt.legend()

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
