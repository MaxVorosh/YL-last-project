from flask import Flask, render_template, redirect

app = Flask(__name__)
app.config["SECRET_KEY"] = "asdftgyhujoijhmg"


@app.route("/")
@app.route("/index")
def index():
    return render_template("general.html")


if __name__ == "__main__":
    app.run()
