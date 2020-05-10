from data.forms import RegistrationForm, LoginForm, AddProductForm, AuctionForm, SearchForm, BuyForm
from flask_login import login_user, logout_user, current_user, LoginManager, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from data import db_session, Users, Products, Auctions, Deals
from data.forms import DealForm, CloseForm, AcceptForm
from flask import Flask, render_template, redirect
from random import choice, randint
import datetime
import os


def my_hash(s):
    """
    Функция для создания секретного ключа по ключу в файле.
    """
    data_p = [10 ** 9 + 7, 10 ** 9 + 9, 998244353]
    data_step = [239, 713, 53]
    p = choice(data_p)
    step = choice(data_step)
    added = randint(0, 100)
    rez = ord(s[0]) + added
    for i in range(1, len(s)):
        rez = (rez * step + ord(s[i]) + added) % p
    return rez


app = Flask(__name__)  # Создание переменной приложения.
f = open('Config.txt')  # Файл с ключом.
app.config["SECRET_KEY"] = str(my_hash(f.readline()))  # Секретный ключ.
app.config["UPLOAD_FOLDER"] = "static/image/users"  # Папка для загрузки фотографий прользователей.
login_manager = LoginManager()  # Менеджер для Flask-login.
login_manager.init_app(app)  # Инициализация.


@app.errorhandler(401)
def unauthorized(error):
    return render_template('no_access.html'), 401


@app.route("/")
@app.route("/index")
def index():
    """
    Базовая страница.
    """
    session = db_session.create_session()  # Создание сессии.
    return render_template("index.html", current_user=current_user, session=session,
                           Product=Products.Product)


@app.route("/accept_deal/<int:deal_id>", methods=["GET", "POST"])
@login_required
def accept_deal(deal_id):
    """
    Страница приёма сделки владельцем.
    """
    # id сделки
    form = AcceptForm()  # Форма приёма.
    session = db_session.create_session()  # Создание сессии.
    deal = session.query(Deals.Deal).get(deal_id)  # Нахождение сделки в базе данных.
    prod = session.query(Products.Product).get(deal.product)  # Объект заключения сделки.
    from_user = session.query(Users.User).get(int(deal.participants.split(';')[0]))  # Владелец.
    to_user = session.query(Users.User).get(int(deal.participants.split(';')[1]))  # Предлагающий.
    if from_user.id != current_user.id:  # Если сделку пытается принять не владелец.
        return render_template("no_access.html")  # Страница отказа.
    if form.yes.data:  # Если принимается предложение.
        deal.date = datetime.datetime.now()  # Обновляется дата заключени.
        prod.owner = to_user.id  # Права владения переходят другому.
        to_user.products = ';'.join(to_user.products.split(';') + [str(prod.id)])  # Покупающий
        # получает товар.
        from_user.money += int(deal.history)  # Переход виртуальной валюты от купившего бывшему
        # владельцу.
        from_user.products = ';'.join(list(filter(
            lambda x: int(x) != prod.id, from_user.products.split(';'))))  # Исключение у бывшего
        # владельца продукта.
        prod.is_sold = True  # Товар помечается как проданный.
        session.commit()  # Коммит в базу данных.
        if current_user.deals is not None and current_user.deals != "":
            ddeals = current_user.deals.split(';')
            for ddeal in ddeals:  # Перебор всех сделок владельца.
                if int(ddeal) == deal.id:  # Если id совпадают.
                    continue  # Пропуск.
                ddeal = session.query(Deals.Deal).get(int(ddeal))  # Получение сделки.
                if ddeal.product == prod.id:  # Если объект сделки тот же, что и в закончившемся
                    # аукционе
                    session.delete(ddeal)  # Сделка удаляется.
                current_user.deals = ";".join(
                    [i for i in current_user.deals.split(';') if i != ddeal])
                # Обновление списка сделок.
        session.commit()  # Коммит в базу данных.
        auc = session.query(Auctions.Auction).get(prod.id)  # Поиск аукциона по товару.
        if auc is not None:  # Если аукцион по товару существует.
            session.delete(auc)  # Удаление аукциона.
        session.commit()  # Коммит в базу данных.
        return redirect(f"/product/{prod.id}")  # Переход на страницу товара.
    if form.no.data:  # Если предложение отклоняется.
        to_user.money += int(deal.history)  # Деньги возвращаются попытвшемуся купить.
        from_user.deals = ';'.join(list(filter(
            lambda x: int(x) != deal_id, from_user.deals.split(';'))))  # Удаляется сделка у
        # владельца.
        to_user.deals = ';'.join(list(filter(lambda x: int(x) != deal_id, to_user.deals.split(';'))))
        # Удаляется сделка у покупавшего.
        session.delete(deal)  # Удаление сделки из базы данных.
        session.commit()  # Коммит в базу данных.
        return redirect("/account")  # Переход на свою страницу (владельца).
    return render_template("accept_deal.html", message='', current_user=current_user, form=form,
                           product=prod, money=int(deal.history))  # Отображение страницы.


@app.route("/account")
@login_required
def account():
    """
    Страница пользователя.
    """
    session = db_session.create_session()  # Создание сессии.
    deals = []  # Список для сделок, которые есть у пользователя.
    if current_user.deals is not None and current_user.deals.strip() != "":  # Проверка того, есть
        # ли у пользователя сделки.
        for deal in current_user.deals.split(";")[::-1]:  # Перебор каждой сделки.
            deal = session.query(Deals.Deal).filter(Deals.Deal.id == deal).first()  # Нахождение
            # сделки в базе данных.
            curr = session.query(Products.Product).filter(
                Products.Product.id == deal.product).first()  # Нахождение товара в базе данных.
            title = curr.title  # Название товара.
            if len(title) > 25:  # Проверка длины названия.
                title = title[0:24] + "..."  # Если оно слишком длинное -- обрезается.
            if int(deal.participants.split(";")[0]) != current_user.id:  # Проверка того, какой
                # стороной в сделке является пользователь.
                partner = int(deal.participants.split(";")[0])  # Если покупателем.
            else:  # В ином случае.
                partner = int(deal.participants.split(";")[1])  # Если владельцем.
            user = session.query(Users.User).filter(Users.User.id == partner).first()  # Нахождение
            # аккаунта партнёра.
            check = "Подтверждено" if curr.is_sold else "Не подтверждено"  # Проверка осуществления
            # сделки.
            accept = True if curr.owner == current_user.id and check == "Не подтверждено" else False
            # Провекра возможности подтвердить сделку. Это может сделать только владелец.
            deals += [[deal.product, title, user.name, user.surname,
                       deal.date, check, accept, deal.id]]  # Добавление в список сделок информации.
    return render_template("account.html", current_user=current_user, session=session,
                           Product=Products.Product, Deal=Deals.Deal, User=Users.User,
                           account=current_user, enumerate=enumerate, deals=deals,
                           len=len)  # Отображение.


@app.route("/account/<int:acc_id>")
def account_user(acc_id):
    """
    Функция просмотра иного аккаунта.
    """
    session = db_session.create_session()  # Создание сессии.
    user = session.query(Users.User).get(acc_id)  # Поиск пользователя.
    if user is None:  # Если такого пользователя нет.
        return redirect("/")  # Переход на главную страницу.
    if current_user.is_authenticated:  # Если просматривающий пользователь авторизован.
        if acc_id == current_user.id:  # Если это его аккаунт.
            return redirect("/account")  # Переход на страницу.
    return render_template("user.html", session=session, user=user, Product=Products.Product,
                           products=user.products.split(';'))  # Отображение.


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    """
    Страница добавления продукта.
    """
    form = AddProductForm()  # Форма.
    if form.validate_on_submit():  # При подтверждении.
        session = db_session.create_session()  # Создание сессии.
        photo = form.photo.data  # Получение фото из формы.
        product_to_add = Products.Product()  # Создание класса продукта.
        product_to_add.title = form.title.data  # Добавление названия.
        product_to_add.description = form.description.data  # Добавление описания.
        product_to_add.owner = current_user.id  # Добавление владельца.
        product_to_add.lower = product_to_add.title.lower()  # Добавление поля для поиска продукта.
        session.add(product_to_add)  # Добавление продукта в базу данных.
        session.commit()  # Коммит в базу данных.
        products = session.query(Products.Product).all()  # Получение всех продуктов.
        products = map(lambda x: x.id, products)  # Полуение id продуктов.
        products = str(max(products))  # Получение максимального id.
        photo.save(f"static/image/products/{products}.jpg")  # Сохранение фотографии.
        user = session.query(Users.User).filter(current_user.id == Users.User.id).first()
        # Получение текущего пользователя.
        if user.products and user.products != "":  # Если у него есть продукты.
            user.products += ';' + products  # Добавление к ним id продукта через разделитель.
        else:  # В ином случае.
            user.products += products  # Просто добавление id.
        session.commit()  # Коммит в базу данных.
        return redirect("/account")  # Переход на страницу пользователя.
    return render_template("AddProduct.html", message="", current_user=current_user, form=form)


@app.route("/buy/<int:product_id>", methods=["GET", "POST"])
@login_required
def buy(product_id):
    """
    Страница ставки на товар.
    """
    # id продукта
    # try:
    form = BuyForm()  # Создание формы.
    session = db_session.create_session()  # Создание сессии.
    auc = session.query(Auctions.Auction).filter(Auctions.Auction.product == product_id).first()
    # Выделение аукциона на товар.
    if auc is None:  # Если аукцион отсутствует.
        return redirect(f"/product/{product_id}")  # Переход на страницу продукта.
    pr = session.query(Products.Product).filter(Products.Product.id == product_id)[0]  # Продукт.
    user = session.query(Users.User).filter(Users.User.id == current_user.id)[0]  # Пользователь.
    history = auc.history.split(';')  # История товара.
    cost = int(history[-1])  # Его последняя стоимость.
    if form.validate_on_submit():  # При подтверждении отправки формы.
        money = current_user.money  # Получение суммы денег пользователя.
        if not (form.cost.data > money or form.cost.data < cost + 15):  # Если введена корректная
            # сумма.
            auc.history = ";".join(history + [str(form.cost.data)])  # Дополнение истории аукциона.
            user.money -= form.cost.data  # Отчисление денег в залог за участие.
            try:
                last_user = session.query(Users.User).filter(
                    Users.User.id == int(auc.participants.split(';')[-1]))[0]  # Определение
                # предыдущего участника.
                last_user.money += int(auc.history.split(';')[-1])  # Отчисление ему денег.
            except Exception as error:
                print(error)
            auc.participants = ';'.join(
                [i for i in auc.participants.split(";") + [str(current_user.id)] if i.strip() != ""])
            # Добавление пользователя в участников аукциона.
            session.commit()  # Коммит в базу данных.
            return redirect(f"/product/{product_id}")  # Перемещение на страницу товара.
        if form.cost.data < cost + 15:  # Если же новая ставка меньше хотябы суммы 15 у.е. и
            # прошлой ставки.
            return render_template("buy.html",
                                   message='Увеличте предыдущую ставку хотя бы на 15 у.е.',
                                   current_user=current_user, form=form, cost=cost, product=pr)
        # Страница предупреждения.
        return render_template("buy.html", message='Не хватает денег', current_user=current_user,
                               form=form,
                               cost=cost, product=pr)  # Страница предупреждения.
    return render_template("buy.html", message='', current_user=current_user, form=form, cost=cost,
                           product=pr)  # Страница с формой ставки.
    # except Exception as e:
    #     return redirect("/")


@app.route("/close_auction/<int:auc_id>", methods=["GET", "POST"])
@login_required
def close_auction(auc_id):
    """
    Закрытие аукциона.
    """
    # id аукциона
    form = CloseForm()  # Форма закрытия.
    session = db_session.create_session()  # Создание сессии.
    auc = session.query(Auctions.Auction).filter(Auctions.Auction.id == auc_id)[0]  # Поиск
    # текущего аукциона.
    if auc is None:  # Если аукциона нет.
        return redirect(f"/product/{auc_id}")  # Перенаправление на страницу товара.
    if auc.history.split(';')[-1] == "0":  # Если нет ставок, или ставки равны 0.
        session.delete(auc)  # Удаление аукциона.
        session.commit()  # Коммит в базу данных.
        return redirect(f"/product/{auc_id}")  # Перенаправление на страницу товара.
    prod = session.query(Products.Product).filter(Products.Product.id == auc.product)[0]  # Поиск
    # текущего продукта.
    last = auc.participants.split(';')[-1]  # Получение ID последнего участника.
    win = session.query(Users.User).filter(Users.User.id == last)[0]  # Определение победителя.
    win_money = int(auc.history.split(';')[-1])  # Определение суммы победителя.
    user = session.query(Users.User).filter(Users.User.id == current_user.id)[0]  # Получение
    # аккаунта пользователя.
    if prod.owner != user.id:  # Если текущий пользователь -- не владелец.
        return redirect(f"/product/{prod.id}")  # Перемещение на страницу товара.
    if form.submit.data:  # Если ставка подтверждается.
        prod.owner = last  # Владельцем товара становится последний пользователь.
        win.products = ';'.join(win.products.split(';') + [str(prod.id)])  # Добавление товара на
        # страницу победителя.
        user.money += win_money  # Перечисление владельцу финальной суммы.
        deal = Deals.Deal()  # Создание класса сделки.
        deals = session.query(Deals.Deal).all()  # Перебор всех сделок.
        if len(deals) != 0:  # Если они есть.
            deal.id = session.query(Deals.Deal).all()[-1].id + 1  # ID сделки.
        else:  # Если сделок нет.
            deal.id = 1  # Просто приравнивается №1.
        deal.participants = ';'.join([str(current_user.id), str(last)])  # Добавление в сделку
        # победителя и продавца.
        deal.product = prod.id  # Добавление в сделку объекта.
        prod.is_sold = True  # Обновление статуса продажи товара.
        deal.history = win_money  # История сделки состоит только из победной суммы.
        deal.date = datetime.datetime.now()  # Обновление даты.
        session.add(deal)  # Добавление сделки.
        if user.deals is not None and user.deals != "":  # Если сделки пользователя не пусты.
            user.deals = ';'.join(user.deals.split(';') + [str(deal.id)])  # Добавление к текущему
        else:  # В ином случае.
            user.deals = str(deal.id)  # Просто добавление 1.
        # пользователю новой сделки.
        if win.deals is not None and win.deals != "":  # Если сделки победителя не пусты.
            win.deals = ';'.join(win.deals.split(';') + [str(deal.id)])  # Добавление к текущему
        else:  # В ином случае.
            win.deals = str(deal.id)  # Просто приравнивание.
        # сделки.
        session.delete(auc)  # Удаление аукциона.
        if user.deals is not None and user.deals != "":
            ddeals = user.deals.split(';')  # Получение всех сделок пльзователя.
            for ddeal in ddeals:  # Перебор всех сделок владельца.
                if int(ddeal) == deal.id:  # Если заключенная ранее сделка -- та, которая попалась.
                    continue  # Пропуск.
                ddeal = session.query(Deals.Deal).get(int(ddeal))  # Получение сделки.
                if ddeal.product == prod.id:  # Если объект сделки тот же, что и в закончившемся
                    # аукционе
                    session.delete(ddeal)  # Сделка удаляется.
                user.deals = ";".join([i for i in user.deals.split(';') if i != ddeal])
        session.commit()  # Коммит в базу данных.
        return redirect(f"/product/{prod.id}")  # Перенаправление на страницу товара.
    return render_template("close_auction.html", message='', current_user=current_user, form=form,
                           product=prod, money=win_money)  # Страница закрытия аукциона.


@app.route("/delete/<int:product_id>")
def delete(product_id):
    session = db_session.create_session()  # Создание сессии.
    curr_product = session.query(Products.Product).filter(Products.Product.id == product_id).first()
    # Получение текущего товара.
    if curr_product is None:  # Если товар не найден.
        return redirect("/search")  # Перенаправление на страницу поиска.
    if not current_user.is_authenticated or current_user.id != curr_product.owner:  # Если
        # пользователь не авторизован или не является владельцем.
        return redirect(f"/product/{product_id}")  # Перенаправление на страницу товара.
    user = session.query(Users.User).get(current_user.id)  # Получение текущего пользователя.
    auc = session.query(Auctions.Auction).get(product_id)  # Получение аукциона.
    if auc is not None:  # Если аукцион существует.
        session.delete(auc)  # Удаление аукциона.
    if current_user.deals is not None and current_user.deals != "":
        ddeals = current_user.deals.split(';')  # Получение всех сделок пльзователя.
        for ddeal in ddeals:  # Перебор всех сделок владельца.
            ddeal = session.query(Deals.Deal).get(int(ddeal))  # Получение сделки.
            if ddeal.product == curr_product.id:  # Если нужный товар.
                session.delete(ddeal)  # Сделка удаляется.
            user.deals = ";".join([i for i in user.deals.split(';') if i != ddeal])  # Удаление
            # сделки у пользователя.
    session.delete(curr_product)  # Удаление товара.
    user.products = ";".join([i for i in user.products.split(';') if int(i) != product_id])
    # Удаление товара у пользователя.
    session.commit()  # Коммит в базу данных.
    return redirect("/account")  # Перенаправление на страницу пользователя.


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    """
    Изменеие профиля.
    """
    if current_user.is_authenticated is False:  # Если пользователь не авторизован.
        return redirect("/register")  # Перенаправление на регистрацию.
    session = db_session.create_session()  # Создание сессии.
    user = session.query(Users.User).get(current_user.id)  # Получение пользователя.
    form = RegistrationForm()  # Создание формы.
    if form.validate_on_submit():  # При подтверждении.
        if form.name.data == "":  # Проверка имени.
            return render_template("edit_profile.html", message="Необходимо ввести имя",
                                   current_user=current_user, form=form)  # Предупреждение.
        if form.surname.data == "":  # Если введена пустая фамилия.
            return render_template("edit_profile.html", message="Необходимо ввести фамилию",
                                   form=form, current_user=current_user)  # Предупреждение.
        if form.login.data == "":  # Проверка ввода логина.
            return render_template("edit_profile.html", message="Необходимо ввести логин (почту)",
                                   current_user=current_user, form=form)  # Предупреждение.
        if form.password.data == "":  # Если введённый пароль пуст.
            return render_template("edit_profile.html", message="Необходимо ввести пароль",
                                   form=form, current_user=current_user)  # Перенаправление на
        # страницу с предупреждением.
        if form.password.data == "":  # Если введённый пароль пуст.
            return render_template("edit_profile.html", message="Необходимо ввести пароль",
                                   form=form, current_user=current_user)  # Перенаправление на
        # страницу с предупреждением.
        if form.password.data != form.confirm_password.data or form.confirm_password.data == "":
            # Проверка на совпадение паролей.
            return render_template("edit_profile.html", message="Пароли не совпадают", form=form,
                                   current_user=current_user)  # Перенаправление на
        # страницу с предупреждением.
        if check_password_hash(user.password, form.password.data):  # Проверка пароля.
            user.name = form.name.data  # Обновление имени.
            user.surname = form.surname.data  # Обновление фамилии.
            user.login = form.login.data  # Обновление логина.
            if form.photo.data:  # Если прислана фотография.
                filename = form.photo.data.filename  # Получение имени файла.
                form.photo.data.save(
                    "static/image/users/" + form.login.data + "." + filename.split(".")[-1])
                # Сохранение фотографии.
                user.photo = form.photo.data.filename.split(".")[-1] if form.photo.data else ""
            session.commit()  # Коммит в базу данных.
            logout_user()  # Выход пользователя из аккаунта.
            login_user(user)  # Вход с обновлёнными данными.
            return redirect("/account")  # Перенаправление на страницу аккаунта.
        return render_template("edit_profile.html", message="Ложный пароль", form=form,
                               current_user=current_user)  # Страница с предупреждением.
    return render_template("edit_profile.html", current_user=current_user, form=form, message="")


@app.route("/inventory")
@login_required
def inventory():
    """
    Инвентарь пользователя.
    """
    session = db_session.create_session()  # Создание сессии.
    inv = session.query(Products.Product).filter(Products.Product.owner == current_user.id)[::-1]
    # Получение всех предметов.
    inv = list(
        map(lambda x: (("static\\image\\products\\" + str(x.id) + ".jpg"), x), inv))  # Получение
    # изображений.
    return render_template('inventory.html', current_user=current_user, inventory=inv)  # Отображение


@login_manager.user_loader
def load_user(user_id):
    """
    Загрузка пользователя. Flask-login.
    """
    session = db_session.create_session()  # Создани сессии.
    return session.query(Users.User).get(user_id)  # Возвращение пользователя.


@app.route("/login", methods=["POST", "GET"])
def login():
    """
    Вход в аккаунт.
    """
    form = LoginForm()  # Создание формы.
    if form.validate_on_submit():  # При подтверждении формы.
        if form.login.data == "":  # Если логин пользователя пуст.
            return render_template("login.html", current_user=current_user, form=form,
                                   message="Необходимо ввести логин.")  # Страница с предупреждением.
        if form.password.data == "":  # Если пусто поле пароля.
            return render_template("login.html", current_user=current_user, form=form,
                                   message="Необходимо ввести пароль.")  # Предупреждение.
        session = db_session.create_session()  # Создание сессии.
        user = session.query(Users.User).filter(Users.User.email == form.login.data).first()
        # Нахождение пользователя.
        if user is None:  # Если пользователя с подобный логином нет.
            return render_template("login.html", current_user=current_user, form=form,
                                   message="Пользователя с подобной почтой не существует.")
        # Предупреждение.
        if check_password_hash(user.password, form.password.data):  # Проверка пароля.
            login_user(user, remember=form.remember.data)  # Вход.
            return redirect("/")  # Перенаправление на главную страницу.
        return render_template("login.html", current_user=current_user, form=form,
                               message="Ложный пароль.")  # Предупреждение.
    return render_template("login.html", current_user=current_user, form=form, message="")  # Сайт.


@app.route("/logout")
@login_required
def logout():
    """
    Выход пользователя из системы.
    """
    logout_user()  # Flask-login выход.
    return redirect("/")  # Перенаправление на главную страницу.


@app.route("/make_deal/<int:deal_id>", methods=["GET", "POST"])
@login_required
def make_deal(deal_id):
    """
    Создание сделки.
    """
    session = db_session.create_session()  # Создание сессии.
    curr_product = session.query(Products.Product).get(deal_id)  # Получение текущего товара.
    owner = session.query(Users.User).get(curr_product.owner)  # Получение владельца.
    cur = session.query(Users.User).get(current_user.id)  # Получение текущего пользователя.
    if session.query(Auctions.Auction).get(curr_product.id) is not None:  # Если есть аукцион на
        # товар.
        return redirect(f"/product/{deal_id}")  # Перенаправление на страницу товара.
    form = DealForm()  # Получение формы сделки.
    if form.validate_on_submit():  # При подтверждении формы.
        try:
            cost = int(form.cost.data)  # Перевод стоимости в число.
        except Exception as error:  # Если происходит ошибка.
            print(error)  # Вывод ошибки.
            return render_template("Deal.html", form=form, product=curr_product, owner=owner,
                                   message="Необходимо ввести только число.")  # Предупреждение.
        if cur.money >= cost >= 0:  # Если денег хватает, и введённая сумма больше 0,
            deal = Deals.Deal()  # Создание сделки.
            deal.product = curr_product.id  # Обозначение объекта сделки.
            deal.participants = ';'.join([str(owner.id), str(cur.id)])  # Добавление участников.
            deal.history = str(form.cost.data)  # Добавление истории сделки.
            deal.date = datetime.datetime.now()  # Постановка времени.
            cur.money -= cost  # Отчисление денег в залог.
            session.add(deal)  # Добавление сделки.
            owner.deals = ';'.join(owner.deals.split(';') + [
                str(deal.id)]) if owner.deals else str(deal.id)  # Добавление сделки владельцу.
            cur.deals = ';'.join(
                cur.deals.split(';') + [str(deal.id)]) if cur.deals else str(deal.id)  # Добалвение
            # сделки пользователю.
            session.commit()  # Коммит в базу данных..
            return redirect(f"/product/{curr_product.id}")  # Перенаправление на страницу товара.
        elif cost < 0:  # Если же стоимость ниже 0.
            return render_template("Deal.html", form=form, product=curr_product, owner=owner,
                                   message="Это не нефть.")  # Предупреждение.
        else:  # В ином случае.
            return render_template("Deal.html", form=form, product=curr_product, owner=owner,
                                   message="У вас нет такого числа денег")  # Предупреждение.
    return render_template("Deal.html", form=form, product=curr_product, owner=owner, message="")


@app.route("/new_auction/<int:pr_id>")
@login_required
def new_auction_product(pr_id):
    """
    Добавление аукциона вокруг товара.
    """
    session = db_session.create_session()  # Создание сессии.
    curr = session.query(Products.Product).get(pr_id)  # Получение продукта.
    if curr.is_sold == 1:  # Если продукт продан.
        return redirect(f"/product/{pr_id}")  # Перенаправление на страницу товара.
    auction = session.query(Auctions.Auction).get(pr_id)  # Получение аукциона.
    if auction is not None:  # Если аукцион существует.
        return redirect(f"/buy/{pr_id}")  # Перенаправление на страницу товара.
    auction = Auctions.Auction()  # Создание аукциона.
    auction.id = pr_id  # Установка id.
    auction.product = auction.id  # Установка продукта.
    auction.participants = ""  # Установка участников.
    auction.history = "0"  # Установка истории.
    session.add(auction)  # Добавление аукциона.
    session.commit()  # Коммит в базу данных.
    return redirect(f"/product/{pr_id}")  # Перенаправление на страницу товара.


@app.route("/product/<int:pr_id>")
def product(pr_id):
    """
    Страница продукта.
    """
    session = db_session.create_session()  # Создание сессии.
    pr = session.query(Products.Product).filter(Products.Product.id == pr_id).first()  # Получение
    # продукта.
    if pr is None:  # Если товар отсутствует.
        return redirect("/search")  # Перенаправление на страницу поиска.
    owner = session.query(Users.User).get(pr.owner)  # Получение владельца.
    auction = session.query(Auctions.Auction).get(pr_id)  # Получение аукциона.
    if auction is None:  # Если нет аукциона.
        auction = -1  # Перевод в обозначение.
    return render_template("product.html", product=pr, owner=owner, current_user=current_user,
                           auction=auction)  # Отображение.


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Регистрация.
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.name.data == "":  # Проверка ввода имени.
            return render_template("register.html", message="Необходимо ввести имя",
                                   current_user=current_user, form=form)  # Предупреждение.
        if form.surname.data == "":  # Проверка ввода фамилии.
            return render_template("register.html", message="Необходимо ввести фамилию", form=form,
                                   current_user=current_user)  # Предупреждение.
        if form.login.data == "":  # Проверка ввода логина.
            return render_template("register.html", message="Необходимо ввести логин (почту)",
                                   current_user=current_user, form=form)  # Предупреждение.
        if form.password.data == "":  # Если введённый пароль пуст.
            return render_template("register.html", message="Необходимо ввести пароль",
                                   form=form, current_user=current_user)  # Перенаправление на
        # страницу с предупреждением.
        if form.password.data != form.confirm_password.data or form.confirm_password.data == "":
            # Проверка ввода подтверждения и совпадения паролей.
            return render_template("register.html", message="Пароли не совпадают", form=form,
                                   current_user=current_user)  # Предупреждение.
        session = db_session.create_session()  # Создание сессии.
        if form.photo.data:  # Если получена фотография.
            filename = form.photo.data.filename  # Получение имени.
            form.photo.data.save(
                "static/image/users/" + form.login.data + "." + filename.split(".")[-1])
            # Сохранение фотографии.
        if session.query(Users.User).filter(Users.User.email == form.login.data).first() is not None:
            # Проверка использования логина.
            return render_template("register.html", message="Подобный email уже используется.",
                                   current_user=current_user, form=form)  # Предупреждение.
        user = Users.User()  # Создание пользователя.
        user.email = form.login.data  # Установка почты.
        user.password = generate_password_hash(form.password.data)  # Установка пароля.
        user.name = form.name.data  # Установка имени.
        user.surname = form.surname.data  # Установка фамилии.
        user.money = 50.0  # Установка количества денег.
        user.photo = form.photo.data.filename.split(".")[-1] if form.photo.data else ""  # Установка
        # фото.
        session.add(user)  # Добавление пользователя.
        session.commit()  # Коммит в базу данных.
        login_user(user)  # Вход.
        return redirect("/")  # Предупреждение на главную страницу.
    return render_template("register.html", message="", current_user=current_user, form=form)


@app.route("/search", methods=["GET", "POST"])
def search():
    """
    Поиск товаров.
    """
    form = SearchForm()  # Создание формы.
    session = db_session.create_session()  # Создание сессии.
    if form.search.data and form.product.data:  # Если введено только название.
        good = session.query(Products.Product).filter(Products.Product.lower.like(
            f"%{form.product.data.lower()}%"), Products.Product.is_sold == 0)  # Писк товаров.
        inv = list(
            map(lambda x: (("static\\image\\products\\" + str(x.id) + ".jpg"), x), good))  # Поиск
        # фотографий.
        return render_template("Search.html", message='', current_user=current_user, form=form,
                               inventory=inv)  # Отображение.
    if form.submit.data and form.product.data and form.number.data:  # Если введены все поля.
        session = db_session.create_session()  # Создание сессии.
        good = session.query(Products.Product).filter(Products.Product.lower.like(
            f"%{form.product.data.lower()}%"), Products.Product.is_sold == 0)  # Поиск товаров.
        try:
            return redirect(f"/product/{good[form.number.data - 1].id}")  # Перенаправление на
        # страницу товара.
        except Exception as error:
            print(error)  # Вывод ошибки.
            return render_template("Search.html", message='Введите действительный номер',
                                   current_user=current_user,
                                   form=form, inventory=[])  # Предупреждение.
    return render_template("Search.html", message='', current_user=current_user, form=form,
                           inventory=[])  # Отображение.


if __name__ == "__main__":  # Проверка прямого запуска.
    db_session.global_init("db/database.sqlite")  # Инициализация базы данных.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))  # Запуск программы.
