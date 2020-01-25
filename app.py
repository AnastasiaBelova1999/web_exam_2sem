import json

import mysql
from flask import Flask, render_template, request, abort, redirect, flash, url_for
from flask_login import login_required
from collections import namedtuple

from mysql_db import MySQL
import mysql.connector
import flask_login
import hashlib

app = Flask(__name__)
app.secret_key = 'asjdfbajSLDFBhjasbfd'
app.config.from_pyfile('config.py')
db = MySQL(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(login):
    cursor = db.db.cursor(named_tuple=True)
    cursor.execute('select id, login from users where id = %s', (login,))
    user_db = cursor.fetchone()
    if user_db:
        user = User()
        user.id = user_db.id
        user.login = user_db.login
        return user
    return None


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("index.html", authorization=False, login="anonimus", login_false=False)


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    if request.method == 'GET':
        login: str
        if flask_login.current_user.is_anonymous:
            login = "anonymus"
        else:
            login = flask_login.current_user.login
        return render_template("index.html", authorization=not flask_login.current_user.is_anonymous, login=login)
    elif request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = hashlib.sha224(password.encode()).hexdigest()
        if username and password:
            cursor = db.db.cursor(named_tuple=True, buffered=True)
            try:
                cursor.execute(
                    "SELECT id,login FROM users_exam WHERE `login` = '%s' and `password_hash` = '%s'" % (
                        username, password_hash))
                user = cursor.fetchone()
            except Exception:
                cursor.close()
                return render_template("index.html", authorization=False,
                                       login="anonimus", login_false=True)
            cursor.close()
            if user is not None:
                flask_user = User()
                flask_user.id = user.id
                flask_user.login = user.login
                flask_login.login_user(flask_user, remember=True)
                return render_template("index.html", authorization=not flask_login.current_user.is_anonymous,
                                       login=user.login, login_false=False)
            else:
                flash("Не правильный логин или пароль")
                return render_template("index.html", authorization=False,
                                       login="anonimus", login_false=True)
        else:
            flash("Не правильный логин или пароль")
            return render_template("index.html", authorization=False,
                                   login="anonimus", login_false=True)

@app.route('/logout', methods=['GET'])
def logout():
    flask_login.logout_user()
    return render_template("index.html", authorization=not flask_login.current_user.is_anonymous, login="anonimus",
                           login_false=False)

@app.route('/list', methods=['GET'])
@login_required
def list():
    lists = db.select(None, "lists")
    login = flask_login.current_user.login
    types = dict(db.select(None, "types"))
    statuss = dict(db.select(["id", "title"], "statuss"))

    view_lists = []
    for list in lists:
        view_lists.append({"id": list.id,
                          "data": list.data,
                          "login_users": list.login_users,
                          "type": type[list.type_id],
                          "status": type [list.status_id],
                          "message": list.message,
                          "type_id": list.type_id,
                          "status_id": list.status_id
                          })
    return render_template("call-list.html", login=login, lists=view_lists)

@app.route('/list/delete', methods=['POST'])
@login_required
def list_delete():
    id = request.form.get("id")
    cursor = db.db.cursor()
    cursor.execute("DELETE FROM `lists` WHERE `lists`.`id` = '%s'" % id)
    cursor.close()
    return redirect("/list")



if __name__ == '__main__':
    app.run()
