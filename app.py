
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
app.debug = True
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
    status = dict(db.select(["id", "title"], "status"))
    return render_template("call-list.html", login=login, lists=lists)

@app.route('/list/delete', methods=['POST'])
@login_required
def list_delete():
    id = request.form.get("id")
    cursor = db.db.cursor()
    cursor.execute("DELETE FROM `lists` WHERE `lists`.`id` = '%s'" % id)
    cursor.close()
    return redirect("/list")

@app.route('/list/new', methods=['POST', 'GET'])
@login_required
def sub_new():
    if request.method == 'GET':
        types = db.select(["id", "title"], "types")
        status = db.select(["id", "title"], "status")
        return render_template("new.html", types=types, status=status)
    elif request.method == 'POST':
        id = request.form.get("id")
        data = request.form.get("data")
        login_users = request.form.get("login_users")
        type_id = request.form.get("types")
        status_id = request.form.get("status")
        if id and data and login_users and type_id and status_id:
            cursor = db.db.cursor(named_tuple=True)
            try:
                cursor.execute(
                    "INSERT INTO `subscribers` (`id`, `data`, `login_users`, `type_id`,`status_id`) VALUES ('%s', '%s', '%s', '%s','%s')" % (
                        id, data,login_users, type_id, status_id))
                db.db.commit()
                cursor.close()
                return redirect("new.html")
            except Exception:
                return render_template("new.html", login=flask_login.current_user.login, insert_false=True)
        else:
            return render_template("new.html", login=flask_login.current_user.login, insert_false=True)

    @app.route('/list/edit', methods=['POST'])
    @login_required
    def list_edit():
        if flask_login.current_user.role_id is not [1, 2]:
            redirect("/")
        try:
            id = request.form.get("id")
            date = request.form.get("date")
            message = request.form.get("message")
            status_id = request.form.get("status_id")
            type_id = request.form.get("type_id")
            user_id = request.form.get("user_id")
            statuss = db.select(None, "status_request")
            types = db.select(None, "type_request")
            req = {
                'id': id,
                'date': date,
                'message': message,
                'status_id': status_id,
                'type_id': type_id,
                'older_id': id
            }
            return render_template("list_edit.html", req=req, types=types, statuss=statuss,
                                   login=flask_login.current_user.login, user_id=user_id,
                                   user_role=flask_login.current_user.role_id)
        except Exception:
            return redirect(url_for("req", error=True))

    @app.route('/list/edit/submit', methods=['POST'])
    @login_required
    def list_edit_submit():
        older_id = request.form.get("older_id")
        date = request.form.get("date")
        status_id = request.form.get("status_id")
        type_id = request.form.get("type_id")
        message = request.form.get("message")
        if date and older_id and status_id and type_id and message:
            cursor = db.db.cursor(named_tuple=True)
            try:
                cursor.execute(
                    "UPDATE `request` SET  `date` = '%s', `status_id` = '%s',`type_id` = '%s',`message` = '%s' WHERE `request`.`id` = %s" % (
                        date, status_id, type_id, message, older_id))
                db.db.commit()
                cursor.close()
                return redirect(url_for("call-esit"))
            except Exception:
                return redirect(url_for("call-list", error=True))
        else:
            return redirect(url_for("call-list", error=True))


if __name__ == '__main__':
    app.run()
