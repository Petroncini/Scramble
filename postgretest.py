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

db = SQL("postgresql://scramble_db_user:NIhnBoM5P7INOwWuGoA0Lp0PcyGW67Qi@dpg-cn2ick7109ks73974sbg-a.oregon-postgres.render.com/scramble_db")

data = db.execute("SELECT* FROM schedule WHERE user_id = 2")

print(data)