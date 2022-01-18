from flask import Flask, render_template, request, flash, session, redirect, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_session import Session
from flask_paginate import Pagination

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'rec_system'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template("index.html")


# @app.route('/home', defaults={'pagenumber': 1})
# @app.route('/home/<int:pagenumber>')
@app.route('/home')
def home():
    if not session.get("loggedin"):
        return redirect("/")
    page = int(request.args.get("page", 1))
    rows_per_page = 5
    offset = (page - 1) * rows_per_page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM book')
    total = cursor.fetchall()
    cursor.execute('SELECT * FROM book LIMIT % s OFFSET % s', (rows_per_page, offset,))
    books = cursor.fetchall()
    paginate = Pagination(page=page, total=len(total))
    return render_template("home.html", books=books, paginate=paginate, allbooks=total)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            flash('Incorrect email / password !')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect("/")


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        surname = request.form['surname']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = % s', (username,))
        userusername = cursor.fetchone()

        cursor.execute('SELECT * FROM user WHERE email = % s', (email,))
        useremail = cursor.fetchone()
        if userusername:
            flash('Username already exists !')
        if useremail:
            flash('Email already exists !')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address !')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers !')
        else:
            cursor.execute('INSERT INTO user (name, surname, username, email, password) VALUES (% s, % s, % s, % s, '
                           '% s)', (name, surname, username, email, password))
            mysql.connection.commit()
            flash('You have successfully registered !')
    return render_template('signup.html')


@app.route('/addFavorites/<int:id>', methods=["GET", "POST"])
def addFavorites(id):
    if not session.get("loggedin"):
        return redirect("/")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM book WHERE id = % s', (id,))
    book = cursor.fetchone()
    bookID = book['bookID']
    userID = session['id']

    cursor.execute('INSERT INTO userfavorites (bookID, userID) VALUES (% s, % s)', (bookID, userID))
    mysql.connection.commit()
    return redirect((url_for('home')))


@app.route('/favorites')
def favorites():
    if not session.get("loggedin"):
        return redirect("/")
    userID = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM book b, userfavorites f WHERE f.userID = % s AND f.bookID = b.bookID', (userID,))
    favbooks = cursor.fetchall()

    return render_template("favorites.html", favbooks=favbooks)


@app.route('/removeFavorite/<int:id>', methods=["GET", "POST"])
def removeFavorite(id):
    if not session.get("loggedin"):
        return redirect("/")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM userfavorites WHERE bookID = % s', (id,))
    mysql.connection.commit()
    return redirect(url_for("favorites"))


if __name__ == "__main__":
    app.run(debug=True)
