from data import db_session, Users, Products, Auctions, Deals
from data.forms import RegistrationForm, LoginForm, AddProductForm, AuctionForm, SearchForm, BuyForm, DealForm
from flask_login import login_user, logout_user, current_user, LoginManager, login_required
from flask import Flask, render_template, redirect, request
from random import choice, randint
import sqlalchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


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
f = open('Config.txt')
app.config["SECRET_KEY"] = str(my_hash(f.readline()))
app.config["UPLOAD_FOLDER"] = "static/image/users"
login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/account")
@login_required
def account():
    session = db_session.create_session()
    return render_template("account.html", current_user=current_user, session=session,
                           Product=Products.Product,
                           Deal=Deals.Deal, User=Users.User, account=current_user)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(Users.User).get(user_id)


@app.route("/")
@app.route("/index")
def index():
    session = db_session.create_session()
    products = session.query(Products.Product).all()[::-1][:10]
    return render_template("index.html", current_user=current_user, session=session,
                           Product=Products.Product)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(Users.User).filter(Users.User.email == form.login.data).first()
        if user is None:
            return render_template("login.html", current_user=current_user, form=form,
                                   message="Пользователя с подобной почтой не существует.")
        if check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect("/")
        return render_template("login.html", current_user=current_user, form=form,
                               message="Ложный пароль.")
    return render_template("login.html", current_user=current_user, form=form, message="")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        if form.photo.data:
            filename = form.photo.data.filename
            form.photo.data.save(
                "static/image/users/" + form.login.data + "." + filename.split(".")[-1])
        if session.query(Users.User).filter(Users.User.email == form.login.data).first() is not None:
            return render_template("register.html", message="Подобный email уже используется.",
                                   current_user=current_user, form=form)
        if form.password.data != form.confirm_password.data:
            return render_template("register.html", message="Пароли не совпадают.",
                                   current_user=current_user,
                                   form=form)
        user = Users.User()
        user.email = form.login.data
        user.password = generate_password_hash(form.password.data)
        user.name = form.name.data
        user.surname = form.surname.data
        user.photo = form.photo.data.filename.split(".")[-1] if form.photo.data else ""
        session.add(user)
        session.commit()
        login_user(user)
        return redirect("/")
    return render_template("register.html", message="", current_user=current_user, form=form)


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def AddProduct():
    # TODO сделать дизайн и переход на эту страницу с других
    form = AddProductForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        photo = form.photo.data
        product = Products.Product()
        product.title = form.title.data
        product.description = form.description.data
        product.owner = current_user.id
        product.lower = product.title.lower()
        session.add(product)
        session.commit()
        id = session.query(Products.Product).all()
        id = map(lambda x: x.id, id)
        id = str(max(id))
        photo.save(f"static/image/products/{id}.jpg")
        user = session.query(Users.User).filter(current_user.id == Users.User.id).first()
        if user.products:
            user.products += '; ' + id
        else:
            user.products += id
        session.commit()
        return redirect("/account")
    return render_template("AddProduct.html", message="", current_user=current_user, form=form)


@app.route("/search", methods=["GET", "POST"])
@login_required
def Search():
    form = SearchForm()
    session = db_session.create_session()
    if form.search.data and form.product.data:
        good = session.query(Products.Product).filter(Products.Product.title == form.product.data)
        inventory = list(
            map(lambda x: (("static\\image\\products\\" + str(x.id) + ".jpg"), x), good))
        return render_template("Search.html", message='', current_user=current_user, form=form,
                               inventory=inventory)
    if form.submit.data and form.product.data and form.number.data:
        session = db_session.create_session()
        good = session.query(Products.Product).filter(Products.Product.title == form.product.data)
        try:
            return redirect(f"/product/{good[form.number.data - 1].id}")
        except Exception:
            return render_template("Search.html", message='Введите действительный номер',
                                   current_user=current_user,
                                   form=form, inventory=[])
    return render_template("Search.html", message='', current_user=current_user, form=form,
                           inventory=[])


@app.route("/inventory")
@login_required
def Inventory():
    session = db_session.create_session()
    inventory = session.query(Products.Product).filter(Products.Product.owner == current_user.id)
    inventory = list(
        map(lambda x: (("static\\image\\products\\" + str(x.id) + ".jpg"), x), inventory))
    return render_template('inventory.html', current_user=current_user, inventory=inventory)


@app.route("/new_auction", methods=["GET", "POST"])
@login_required
def new_auction():
    form = AuctionForm()
    if form.search.data and form.product.data:
        session = db_session.create_session()
        good = session.query(Products.Product).filter(Products.Product.lower.like(f"%{form.product.data.lower()}%"))
        inventory = list(
            map(lambda x: (("static\\image\\products\\" + str(x.id) + ".jpg"), x), good))
        return render_template("AddAuction.html", message='', current_user=current_user, form=form,
                               inventory=inventory)
    if form.submit.data and form.product.data and form.number.data:
        session = db_session.create_session()
        good = session.query(Products.Product).filter(Products.Product.lower.like(f"%{form.product.data.lower()}%"))
        try:
            auction = Auctions.Auction()
            auction.id = good[form.number.data - 1].id
            auction.product = auction.id
            auction.participants = ""
            auction.history = "0"
            session.add(auction)
            session.commit()
            return redirect("/")
        except:
            return render_template("AddAuction.html", message='Введите действительный номер',
                                   current_user=current_user,
                                   form=form, inventory=[])
    return render_template("AddAuction.html", message='', current_user=current_user, form=form,
                           inventory=[])


@app.route("/product/<int:id>")
def product(id):
    session = db_session.create_session()
    pr = session.query(Products.Product).filter(Products.Product.id == id).first()
    if pr is None:
        return redirect("/")
    owner = session.query(Users.User).get(pr.owner)
    return render_template("product.html", product=pr, owner=owner)


@app.route("/account/<int:id>")
def account_user(id):
    session = db_session.create_session()
    user = session.query(Users.User).get(id)
    if user is None:
        return redirect("/")
    if current_user.is_authenticated:
        if id == current_user.id:
            return redirect("/account")
    return render_template("user.html", session=session, user=user, Product=Products.Product)


@app.route("/make_deal/<int:id>", methods=["GET", "POST"])
@login_required
def make_deal(id):
    session = db_session.create_session()
    product = session.query(Products.Product).get(id)
    owner = session.query(Users.User).get(product.owner)
    form = DealForm()
    if form.validate_on_submit():
        pass
    return render_template("Deal.html", form=form, product=product, owner=owner, message="")


@app.route("/buy/<int:id>", methods=["GET", "POST"])
@login_required
def buy(id):
    # id продукта
    # try:
    form = BuyForm()
    session = db_session.create_session()
    auc = session.query(Auctions.Auction).filter(Auctions.Auction.product == id).first()
    pr = session.query(Products.Product).filter(Products.Product.id == id)[0]
    history = auc.history.split(';')
    cost = int(history[-1])
    if form.validate_on_submit():
        money = current_user.money
        if not (form.cost.data > money or form.cost.data < cost + 15):
            auc.history = ";".join(history + [str(form.cost.data)])
            current_user.money -= form.cost.data
            auc.participants = ';'.join([i for i in auc.participants.split(";") + [str(current_user.id)] if i.strip() != ""])
            session.commit()
            return redirect("/")
        if form.cost.data < cost + 15:
            return render_template("buy.html",
                                   message='Увеличте предыдущую ставку хотя бы на 15 у.е.',
                                   current_user=current_user, form=form, cost=cost, product=pr)
        return render_template("buy.html", message='Не хватает денег', current_user=current_user,
                               form=form,
                               cost=cost, product=pr)
    return render_template("buy.html", message='', current_user=current_user, form=form, cost=cost,
                           product=pr)
    # except Exception as e:
    #     return redirect("/")


if __name__ == "__main__":
    db_session.global_init("db/database.sqlite")
    app.run()
