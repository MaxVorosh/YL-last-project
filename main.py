from data import forms, db_session
from flask_login import login_user, logout_user
from flask import Flask, render_template, redirect

app = Flask(__name__)
app.config["SECRET_KEY"] = "asdftgyhujoijhmg"


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/register")
def register():
    pass


if __name__ == "__main__":
    db_session.global_init("db/database.sqlite")
    app.run()
