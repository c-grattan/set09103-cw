from flask import Flask, render_template, request, redirect, url_for, g, session
import bcrypt
import sqlite3
import configparser
import random

from sanitize_input import sanitize
from eq_parsing import calcFunc

def init(app):
	config = configparser.ConfigParser()
	try:
		cfg = "defaults.cfg"
		config.read(cfg)

		app.secret_key = config.get("config", "secret_key")
	except:
		print("Unable to read config from: ", cfg)

app = Flask(__name__)
init(app)

#Database Management
db_location = "var/database.db"
def get_db():
	db = getattr(g, "db", None)
	if db is None:
		db = sqlite3.connect(db_location)
		g.db = db
	return db

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource("var/schema.sql", mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

@app.teardown_appcontext
def destroy_db_connection(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

#Server Routes
@app.route('/')
def index():
	cursor = get_db().cursor()
	featured_equation = random.choice(cursor.execute("SELECT rowid, * FROM equations").fetchall())
	return render_template("index.html", equation=featured_equation), 200

@app.route('/equations/')
def predefined_equations():
	cursor = get_db().cursor()
	eq = cursor.execute("SELECT rowid, * FROM equations WHERE user = -1").fetchall()
	return render_template("predefined_main.html", equations=eq), 200

@app.route('/usermade/')
def custom_equations():
	cursor = get_db().cursor()
	eq = cursor.execute("SELECT rowid, * FROM equations WHERE user != -1").fetchall()
	return render_template("custom_main.html", equations=eq), 200

@app.route('/login/', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template("login.html", form=None), 200
	else:
		name = sanitize(request.form['username'])
		pw = sanitize(request.form['password']).encode("utf-8")

		cursor = get_db().cursor()
		account = cursor.execute('SELECT * FROM users WHERE username = "%s"' % name).fetchone()

		if account is None:
			return render_template("login.html", form=request.form, error="No account exists with that name")

		passw = account[1].encode("utf-8")

		if not bcrypt.checkpw(pw, passw):
			return render_template("login.html", form=request.form, error="Incorrect password")
		
		session['name'] = name
		return redirect(url_for('account', name=name))

@app.route('/register/', methods=['GET', 'POST'])
def register():
	if request.method == 'GET':
		return render_template("register.html", form=None), 200
	else:
		name = sanitize(request.form['username'])
		pw = sanitize(request.form['password']).encode("utf-8")
		valid = sanitize(request.form['passwordvalidate']).encode("utf-8")

		db = get_db()
		cursor = db.cursor()

		#Check for unique username
		if(not cursor.execute('SELECT * FROM users WHERE username = "%s"' % name).fetchone() is None):
			return render_template("register.html", form=request.form, error="Username already in use")

		#Password validation
		if pw != valid:
			return render_template("register.html", form=request.form, error="Passwords do not match")
		else:
			cursor.execute('INSERT INTO users VALUES("{}", "{}")'.format(name, bcrypt.hashpw(pw, bcrypt.gensalt()).decode('utf-8')))
			db.commit()
			return render_template("successful.html", action="Register", url="register"), 200

@app.route('/account/')
@app.route('/account/<name>')
def account(name=None):
	if name == None:
		if 'name' in session:
			return redirect(url_for('account', name=session['name']))
		return redirect(url_for('login'))
	else:
		cursor = get_db().cursor()
		user = cursor.execute('SELECT rowid, * FROM users WHERE username = "%s"' % name).fetchone()
		if not user is None:
			cursor = get_db().cursor()
			eq = cursor.execute("SELECT rowid, * FROM equations WHERE user = '{}'".format(user[0])).fetchall()
			return render_template("account.html", user=user, equations=eq)
		else:
			if 'name' in session and session['name'] == name:
				session.pop('name', None)
			return render_template("account.html", user=("404 Account not found", None, None)), 404

@app.route('/logout/')
def logout():
	session.pop('name', None)
	return render_template("successful.html", action="Logout", url="logout")

@app.route('/create/', methods=['GET', 'POST'])
def create():
	if request.method == 'GET':
		if 'name' in session:
			return render_template("create_equation.html", form=None)
		else:
			return redirect(url_for('login'))
	else:
		db = get_db()
		cursor = db.cursor()

		title = sanitize(request.form['title'])
		definition = sanitize(request.form['definition'])

		#Check title is unique
		if(not cursor.execute('SELECT * FROM equations WHERE title = "%s"' % title).fetchone() is None):
			return render_template("create_equation.html", form=request.form, error="Title already in use")

		#Check definition is unique
		existing = cursor.execute('SELECT * FROM equations WHERE def = "%s"' % definition).fetchone()
		if(not existing is None):
			return render_template("create_equation.html", form=request.form, error="There is already an equation with that definition ({})".format(existing[0]))

		#Add equation to db
		userid = cursor.execute('SELECT rowid FROM users WHERE username = "{}"'.format(session['name'])).fetchone()[0]
		cursor.execute('INSERT INTO equations VALUES("{}", "{}", {})'.format(title, definition, userid))
		db.commit()

		return render_template("successful.html", action="Create Equation", url="create")

@app.route('/equations/<equation>')
def equation(equation=None):
	cursor = get_db().cursor()
	eq = cursor.execute("SELECT * FROM equations WHERE rowid = '{}'".format(equation)).fetchone()
	if eq is not None:
		return render_template("equation.html", equation=eq)
	else:
		return render_template("equation.html", equation=eq), 404

@app.route('/api/<equation>', methods=['POST'])
def apiSolve(equation=None):
	if equation is not None:
		cursor = get_db().cursor()
		eq = cursor.execute("SELECT * FROM equations WHERE rowid = '{}'".format(equation)).fetchone()[1]
		result = calcFunc(eq, request)
		if result:
			return result
		else:
			return "Bad values given", 400
	else:
		return 400

@app.route('/delete/')
@app.route('/delete/<equation>')
def delete(equation=None):
	if(equation==None):
		return redirect(url_for('account'))

	db = get_db()
	cursor = db.cursor()

	eq = cursor.execute("SELECT * FROM equations WHERE rowid = {}".format(equation)).fetchone()
	if(eq==None):
		return redirect(url_for('account'))
	user = cursor.execute("SELECT * FROM users WHERE rowid = {}".format(eq[2])).fetchone()

	if('name' in session and session['name'] == user[0]):
		cursor.execute("DELETE FROM equations WHERE rowid = {}".format(equation))
		db.commit()
		return render_template("successful.html", action="Delete Equation", url="delete")
	else:
		return redirect(url_for('login'))

if __name__ == "__main__":
	app.run()