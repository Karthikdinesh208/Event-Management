import json
import os

from flask import Flask, render_template, request, session, url_for, flash, redirect
from flask_mysqldb import MySQL
import MySQLdb.cursors
from passlib.hash import sha256_crypt

app = Flask(__name__)

with open("db.json", "r") as f:
    data = json.load(f)["data"]

app.secret_key = os.urandom(24)
app.config['MYSQL_HOST'] = data["host"]
app.config['MYSQL_USER'] = data["db_user"]
app.config['MYSQL_PASSWORD'] = data["password"]
app.config['MYSQL_DB'] = data["db_name"]
app.config['MYSQL_PORT'] = data["port"]

mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])      #HOMEPAGE
def home():
    return render_template('index.html')


@app.route('/user_logout')
def user_logout():
       session.clear()
       return redirect(url_for('login'))


@app.route('/admin_logout')
def admin_logout():
       session.clear()
       return redirect(url_for('admin_login'))


@app.route("/feedback", methods=['GET', 'POST'])      #FEEDBACK
def feedback():
    if request.method == 'GET':
        return render_template("feedback.html")
    else:
        if request.method == 'POST':
            name = request.form.get('fname')
            cont = request.form.get('fcont')
            desc = request.form.get('fdesc')
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("""INSERT INTO ufeedback( fname , fcont , fdesc) VALUES(%s,%s,%s) """,
                    (name, cont, desc))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('user_dashboard'))


@app.route('/user_dashboard', methods=['GET', 'POST'])    #USER DASHBOARD
def user_dashboard():
    if request.method == 'GET':
        if "user" in session and session["user"] == True:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute(
                "Select e.eid,e.ename,e.edate,e.evenue,e.edesc,o.oid from event e,organiser o where e.eid =o.eid")
            result = cur.fetchall()
            mysql.connection.commit()
            cur.close()
            return render_template("user_dashboard.html", data=result)
        else:
            return redirect(url_for('login'))
    if request.method == 'POST':
                eid = request.form.get('eid')
                vusn = request.form.get('usn')
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("""INSERT INTO participant(eid, usn) VALUES(%s,%s) """,
                            (eid, vusn))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('user_dashboard'))


@app.route("/user/login", methods=['GET', 'POST'])      #USER LOGIN
def login():
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST':
        usn = request.form.get('usn')
        password = request.form.get('password')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("select * from students where usn=%s", (usn,))
        result = cur.fetchone()
        cur.close()
        if result is not None:
            pas_verify = sha256_crypt.verify(password, result["new_password"])
            if pas_verify == True:
                session["usn"] = result["usn"]
                session["user_phone"] = result['phone']
                session["user"] = True
                return redirect(url_for('user_dashboard'))
            else:
                flash(" Incorrect Password", "error")
                return redirect(url_for("login"))
        else:
            flash("USN not found", "error")
            return redirect(url_for("login"))
    else:
        flash("Some error occured", "error")
        return redirect(url_for("login"))


@app.route('/admin_dashboard/<id>')                        #ADMIN DASHBOARD
def abc():
    if "admin" in session and session["admin"] == True:
        return render_template('edit_event.html')
    else:
        return redirect(url_for('admin_login'))


@app.route("/create", methods=['GET', 'POST'])      #ADMIN CREATE EVENT
def admincreate():
    if request.method == 'GET':
        if "admin" in session and session["admin"] == True:
            return render_template("create.html")
        else:
            return redirect(url_for('admin_login'))
    if request.method == 'POST':
        id = request.form.get('eid')
        name = request.form.get('ename')
        date = request.form.get('edate')
        venue = request.form.get('evenue')
        desc = request.form.get('edesc')
        orid = request.form.get('oid')
        ornm = request.form.get('oname')
        ornum = request.form.get('ophone')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""INSERT INTO event(eid, ename , edate , evenue , edesc) VALUES(%s,%s,%s,%s,%s) """,
                    (id, name, date, venue, desc))
        cur.execute("""INSERT INTO organiser( oid , oname , ophone,eid) VALUES(%s,%s,%s,%s) """,
                    (orid, ornm, ornum, id))
        mysql.connection.commit()
        cur.close()
        flash("Event inserted successfully", "error")
        return redirect(url_for('admin_dashboard'))


@app.route("/user/register", methods=['GET', 'POST'])        #USER REGISTRATION
def register():
    if request.method == 'GET':
        return render_template("registration.html")
    if request.method == 'POST':
        usn = request.form.get('usn')
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        re_password = request.form.get('new_password')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("select usn from students where usn=%s", (usn,))
        result = cur.fetchone()
        cur.close()
        if result is not None:
            flash("USN is already used", "error")
            return redirect(url_for('register'))
        else:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("select name from students where name=%s", (name,))
            result = cur.fetchone()
            cur.close()
            if result is not None:
                flash("Name is already used", "error")
                return redirect(url_for('register'))
            else:
                if password == re_password:
                    hash_pas = sha256_crypt.hash(password)
                    db = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    db.execute("insert into students values(%s,%s,%s,%s,%s)", (usn, name, phone, password, hash_pas))
                    mysql.connection.commit()
                    db.close()
                    flash("User Registered successfully", "success")
                    return redirect(url_for('login'))
                else:
                    flash("Password did not match", "error")
                    return redirect(url_for("register"))


@app.route("/admin_login", methods=['GET', 'POST'])         #ADMIN LOGIN
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')
    if request.method == 'POST':
        adminid = request.form.get('admid')
        password = request.form.get('password')
        if((adminid == 'admin2020') and (password  == 'trishar')):
            session["admin"] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("adminid/password incorrect", "error")
            return redirect(url_for('admin_login'))


@app.route('/admin_dashboard', methods=['GET','POST'])          #ADMIN DASHBOARD
def admin_dashboard():
    if request.method == 'GET':
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("Select * from event e,organiser o where e.eid=o.eid")
        result = cur.fetchall()
        cur.execute("Select a.pid,c.usn,c.name,c.phone,b.eid,b.ename   from participant a,event b,students c where c.usn=a.usn and b.eid = a.eid")
        results = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        if "admin" in session and session["admin"] == True:
            return render_template("admin_dashboard.html", data=result,info=results)
        else:
            return redirect(url_for('admin_login'))


@app.route('/admin_dashboard/edit/<id>')        #EDIT EACH EVENT
def event_edit(id):
            eid = id
            db = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            db.execute("select * from event where eid=%s", (eid,))
            result = db.fetchone()
            db.close()
            if "admin" in session and session["admin"] == True:
                return render_template("edit_event.html", data=result)
            else:
                return redirect(url_for('admin_login'))


@app.route("/admin_dashboard/edit_event/<id>", methods=["POST"])   #UPDATE
def event_update(id):
        eid = id
        ename = request.form["ename"]
        edate = request.form["edate"]
        evenue = request.form["evenue"]
        edesc = request.form["edesc"]
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("update event set ename=%s,edate=%s,evenue=%s, edesc=%s where eid=%s", (ename, edate, evenue, edesc, eid))
        mysql.connection.commit()
        cur.close()
        flash("Event updated Successfully", "success")
        if "admin" in session and session["admin"] == True:
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for('admin_login'))


@app.route('/delete/<id>')    #DELETE
def delete(id):
    eid =id
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("delete from event where eid=%s",(eid,))
    mysql.connection.commit()
    cur.close()
    flash("Event Deleted Successfully", "success")
    if "admin" in session and session["admin"] == True:
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)
