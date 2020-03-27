from data import db_session, users
from data.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, current_user, LoginManager
from flask import Flask, render_template, redirect
from random import choice, randint
from werkzeug.security import generate_password_hash, check_password_hash


def my_hash(s):
    data_p = [10 ** 9 + 7, 10 ** 9 + 9, 998244353]
    data_step = [239, 713, 53]
    p = choice(data_p)
    step = choice(data_step)
    added = randint(0, 100)
    rez = ord(s[0]) + added
    for i in range(1, len(s)):
        rez = (rez * step + ord(s[i]) + added) % p
    return rez


app = Flask(__name__)
app.config["SECRET_KEY"] = "zwsxdcfvgbhnjmksdfghjkl"
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(users.User).get(user_id)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", current_user=current_user)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(users.User).filter(users.User.email == form.login.data).first()
        if user is None:
            return render_template("login.html", current_user=current_user, form=form, message="Пользователя с подобной почтой не существует.")
        if check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect("/")
        return render_template("login.html", current_user=current_user, form=form, message="Ложный пароль.")
    return render_template("login.html", current_user=current_user, form=form, message="")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if session.query(users.User).filter(users.User.email == form.login.data).first() is not None:
            return render_template("register.html", message="Подобный email уже используется.", current_user=current_user, form=form)
        if form.password.data != form.confirm_password.data:
            return render_template("register.html", message="Пароли не совпадают.", current_user=current_user, form=form)
        user = users.User(
            email=form.login.data,
            password=generate_password_hash(form.password.data),
            name=form.name.data,
            surname=form.surname.data,
        )
        session.add(user)
        session.commit()
        login_user(user)
        return redirect("/")
    return render_template("register.html", message="", current_user=current_user, form=form)


if __name__ == "__main__":
    db_session.global_init("db/database.sqlite")
    app.run()
