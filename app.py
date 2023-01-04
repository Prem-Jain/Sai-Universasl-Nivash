from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import timedelta, datetime
import os
from base64 import b64encode

app = Flask(__name__, static_url_path='/static', static_folder='static')

# config
app.config.update(
    DEBUG = True,
    SECRET_KEY = 'SUN_ShPbV_801')

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# silly user model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)

def add_entry(name, date, desc):
        con = sqlite3.connect("SUN.db")
        c = con.cursor()
        try:
            x = (name, date, desc)
            insert = """INSERT INTO events (NAME, DATE, DESC) VALUES (?,?,?);"""
            c.execute(insert, x)
        finally:
            con.commit()
            c.close()
            con.close()

def get_entry():
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        records = c.execute("SELECT * FROM events ORDER BY ID desc").fetchall()
    finally:
        con.commit()
        c.close()
        con.close()
        return records

def search_entry(ide):
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        sql_select_query = "SELECT * FROM events WHERE ID = ?;"
        c.execute(sql_select_query, (ide,))
        record = c.fetchall()
    finally:
        c.close()
        con.close()
    return record

def update_entry(ide, name, date, desc):
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        x = name, date, desc, ide
        update = "UPDATE events SET NAME = ?, DATE = ?, DESC = ? WHERE ID = ?;"
        c.execute(update, x)
    finally:
        con.commit()
        c.close()
        con.close()

def delete_entry(ide):
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        delete = "DELETE FROM events WHERE id = ?;"
        c.execute(delete, (ide,))
    finally:
        con.commit()
        c.close()
        con.close()

def get_image(tableName):
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        records = c.execute("SELECT * FROM " + "T" + str(tableName)).fetchall()
        images = []
        for record in records:
            x = b64encode(record[1])
            images.append([record[0], x.decode("UTF-8")])
    finally:
        con.commit()
        c.close()
        con.close()
    return images
       
def get_events():
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        records = c.execute("SELECT * FROM Gallery ORDER BY ID desc").fetchall()
    finally:
        con.commit()
        c.close()
        con.close()
    return records

class event_login:
    login = False
    def user_in(self):
        self.login = True
    def user_out(self):
        self.login = False
    def get_user(self):
        return self.login
elogin = event_login()

@app.route('/')
@app.route('/home')
def home():
    return render_template("Home.html")

@app.route('/about')
def about():
    return render_template("AboutUs.html")

@app.route('/activities')
@app.route('/events')
def events():
    records = get_entry()
    list_records = []
    for record in records:
        record = list(record)
        x = datetime.strptime(record[2], '%Y-%m-%d')
        record[2] = x.strftime('%A, %d-%b, %Y').upper()
        list_records.append(record)
    return render_template("Events.html", records=list_records, login=elogin.get_user())

@app.route('/gallery')
def gallery():
    events = get_events()
    galleryContent = []
    for event in events:
        images = get_image(event[0])
        galleryContent.append([event[0], event[1], images])
    return render_template("Gallery.html", login=elogin.get_user(), galleryContent=galleryContent)

@app.route('/contact')
def contact():
    return render_template("Contact.html")

@app.route('/developers')
def developers():
    return render_template("Developers.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    database = {'Admin@SUN': 'SUN_2011'}
    records = get_entry()
    if request.method == 'POST':
        name1 = request.form['uname']
        pwd = request.form['psw']
        if name1 in database:
            if database[name1] != pwd:
                return render_template('Events.html', info='Invalid Password', records=records)
            else:
                user = User(name1)
                login_user(user)
                elogin.user_in()
                return redirect('events')
        else:
            return render_template('Events.html', info='Invalid User', records=records)
    return render_template('Events.html', records=records)

@app.route("/add", methods=["POST", "GET"])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        desc = request.form['desc']
        add_entry(name, date, desc)
        return redirect('events')
    return render_template("AdADD.html")

@app.route("/edit/<int:ide>", methods=['POST', 'GET'])
@login_required
def edit(ide):
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        desc = request.form['desc']
        update_entry(ide, name, date, desc)
        return redirect(url_for("events"))
    return render_template("AdEdit.html", record=search_entry(ide))

@app.route("/delete/<int:ide>", methods=['POST', 'GET'])
@login_required
def delete(ide):
    delete_entry(ide)
    return redirect(url_for("events"))

@app.route("/dailyImage", methods=['POST', 'GET'])
@login_required
def dailyImage():
    records = get_entry()
    if request.method == 'POST':
        img = request.files['img']
        img = img.read()
        if os.path.exists("static/images/DailyImage.jpeg"):
          os.remove("static/images/DailyImage.jpeg")        
        with open("static/images/DailyImage.jpeg", 'wb') as file:
            file.write(img)
        return render_template("Events.html", records=records, login=elogin.get_user(), imgInfo = "Image Changed Successfully")
    return redirect(url_for("events"))

@app.route("/addImage/<IDT>", methods=['POST', 'GET'])
@login_required
def addImage(IDT):
    if request.method == 'POST':
        img = request.files['img']
        img = img.read()
        con = sqlite3.connect("SUN.db")
        c = con.cursor()
        try:
            insert = """INSERT INTO """ + "T" + str(IDT) + """ (IMAGE) VALUES (?);"""
            c.execute(insert, (img,))
        finally:
            con.commit()
            c.close()
            con.close()
        return redirect(url_for('gallery'))
    return render_template("AddImage.html", IDT=IDT)
    
@app.route("/create", methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        con = sqlite3.connect("SUN.db")
        c = con.cursor()
        try:
            insert = """INSERT INTO Gallery (Name) VALUES (?);"""
            c.execute(insert, (name,))
            idEvent = c.execute("SELECT MAX(ID) FROM Gallery").fetchall()
            c.execute("""CREATE TABLE '""" + "T" + str(idEvent[0][0]) + """' ("ID"	INTEGER, "IMAGE"	BLOB NOT NULL, PRIMARY KEY("ID" AUTOINCREMENT))""")
        finally:
            con.commit()
            c.close()
            con.close()
        return redirect(url_for('gallery'))
    return render_template("createEvent.html")

@app.route("/delImage/<IDT>/<imgDel>", methods=['POST', 'GET'])
@login_required
def delImage(IDT, imgDel):
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        delete = "DELETE FROM " + "T" + str(IDT) + " WHERE ID = ?;"
        c.execute(delete, (imgDel,))
    finally:
        con.commit()
        c.close()
        con.close()
    return redirect(url_for("gallery"))

@app.route("/delImage/<IDT>", methods=['POST', 'GET'])
@login_required
def delEvent(IDT):
    con = sqlite3.connect("SUN.db")
    c = con.cursor()
    try:
        delete = "Drop Table " + "T" + str(IDT) + " ;"
        c.execute(delete)
        delete = "DELETE FROM Gallery WHERE ID = ?;"
        c.execute(delete, (IDT,))
    finally:
        con.commit()
        c.close()
        con.close()
    return redirect(url_for("gallery"))

@app.route('/logout')
def logout():
    logout_user()
    elogin.user_out()
    return redirect(url_for('events'))

@login_manager.user_loader
def load_user(userid):
    return User(userid)

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=20)
    session.modified = True
    g.user = current_user

if __name__ == '__main__':
    app.run(debug=True)