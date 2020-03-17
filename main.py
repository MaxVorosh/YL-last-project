from flask import Flask, render_template, redirect
from random import choice, randint


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
f = open('Config.txt', 'r')
hash_string = f.readline()
app.config["SECRET_KEY"] = my_hash(hash_string)


@app.route("/")
@app.route("/index")
def index():
    return render_template("general.html")


if __name__ == "__main__":
    app.run()
