from flask import Flask, render_template, request, redirect, url_for, g, session
import bcrypt
import sqlite3
import configparser

from sanitize_input import sanitize

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
	return render_template("index.html"), 200

@app.route('/equations/')
def predefined_equations():
	return render_template("predefined_main.html"), 200

@app.route('/usermade/')
def custom_equations():
	return render_template("custom_main.html"), 200

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
		return render_template("successful.html", action="Login"), 200

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
			return render_template("successful.html", action="Register"), 200

@app.route('/account/')
@app.route('/account/<name>')
def account(name=None):
	if name == None:
		return redirect(url_for('login'))
	else:
		cursor = get_db().cursor()
		user = cursor.execute('SELECT * FROM users WHERE username = "%s"' % name).fetchone()
		if not user is None:
			return render_template("account.html", user=user)
		else:
			return render_template("account.html", user=("404 Account not found", None, None)), 404

@app.route('/logout/')
def logout():
	session.pop('name', None)
	return render_template("successful.html", action="Logout")

if __name__ == "__main__":
	app.run()