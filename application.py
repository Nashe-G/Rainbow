from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from flask_json import json_response, FlaskJSON, JsonTestResponse
from datetime import datetime

from helpers import apology, login_required

app = Flask(__name__)
json = FlaskJSON(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///machines.db")

@app.route("/")
@login_required
def index():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
        # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE user_name = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["ID"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/check_in", methods=["GET", "POST"])
def check_in():
    if request.method == "GET":
        return render_template("check_in.html")
    else:
        #if qr-code scanner does return a result render apology
        result = request.form.get("result")
        if result != None:
            #record time when machine is checked into property
            now = datetime.now()
            lat = request.form.get("Lat")
            longt = request.form.get("Long")
            #indentify user who is cheking in machine
            username = db.execute("SELECT name FROM users WHERE ID = :user_id", user_id = session["user_id"])
            Typ = db.execute("SELECT type FROM Machines WHERE ID = :ID", ID = result)
            username = username[0]["name"]
            Typ = Typ[0]["Type"]
            #update data base giving machine new location and recording details into history.
            db.execute("UPDATE Machines SET User=:user, LAT=:LAT, LONg=:LONG WHERE ID = :machine_id", machine_id = result, user = username, LAT = lat, LONG = longt)
            db.execute("INSERT INTO History (id, User, LAT, LONG, Type, date_time) VALUES (:ID, :user, :LAT, :LONG, :Type, :datetime)",ID =result, user = username, LAT = lat, LONG = longt, Type=Typ, datetime=now)
        else:
            render_template("apolgy.html")
        return render_template("check_in.html")

@app.route("/History", methods=["GET","POST"])
def history():
    if request.method == "GET":
        #admins usernames set
        admin1 = "jonhg"
        admin2 = "tinasheg"
        admin=db.execute("SELECT ID FROM users WHERE user_name = 'tinasheg' OR user_name = 'johng'")
        #only admins can access the history.html page to view machine histories
        if admin[0]['ID'] == session["user_id"] or admin[1]['ID'] == session["user_id"]:
            machines = db.execute("SELECT ID FROM Machines")
            return render_template("history.html", machines = machines)
        else:
            return render_template("apology.html")
    else:
        fanID = request.form.get('fanID')
        #get machine data based on ID chosen by admin
        table = db.execute("SELECT User, LAT, LONG, date_time FROM History  WHERE ID = :fanID", fanID = fanID)
        return render_template("machine_info.html", table = table)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("Add.html")
    else:
        result = request.form.get("result")
        #if qr reader return no results render apology
        if result != None:
            lat = request.form.get("Lat")
            longt = request.form.get("Long")
            typ = request.form.get("type")
            #record user adding machine into database
            username = db.execute("SELECT name FROM users WHERE ID = :user_id", user_id = session["user_id"])
            username = username[0]["name"]
            db.execute("INSERT INTO Machines (id, User, LAT, LONG, Type) VALUES (:machine_id, :user, :LAT, :LONG, :Typ)", machine_id = result, user = username, LAT = lat, LONG = longt, Typ = typ)
            print(result)
        else:
            return render_template("apology.hmtl")
        return render_template("Add.html")


@app.route("/view", methods=["GET", "POST"])
def view():
    if request.method == "GET":
        #get location data from database to put on map.
        markers = db.execute("SELECT ID, LAT, LONG FROM Machines")
        return render_template("view.html", location = markers)
