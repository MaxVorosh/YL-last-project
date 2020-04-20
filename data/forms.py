from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, SubmitField, FileField, IntegerField
from wtforms.validators import DataRequired
from flask_wtf.file import FileRequired, FileAllowed


class LoginForm(FlaskForm):
    login = StringField("Логин (email)", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить в системе", default=False)
    submit = SubmitField("Войти")


class RegistrationForm(FlaskForm):
    login = StringField("Логин (email)", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    confirm_password = PasswordField("Повтор пароля", validators=[DataRequired()])
    name = StringField("Имя", validators=[DataRequired()])
    surname = StringField("Фамилия", validators=[DataRequired()])
    photo = FileField("Фотография (не обязательно) (советуется квадратную)",
                      validators=[FileAllowed(['jpg', 'png', 'jpeg'],
                                              "Файл должен быть одного из этих форматов: 'jpg', 'png', 'jpeg'")])
    submit = SubmitField("Зарегестрироваться")


class AddProductForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    description = StringField("Описание", validators=[DataRequired()])
    photo = FileField("Изображение",
                      validators=[FileRequired(),
                                  FileAllowed(['jpg', 'png', 'jpeg'],
                                              "Файл должен быть одного из этих форматов: 'jpg', 'png', 'jpeg'")])
    submit = SubmitField("Подтвердить")


class AuctionForm(FlaskForm):
    product = StringField("Название предмета", validators=[DataRequired()])
    number = IntegerField("Введите порядковый номер объекта из выбранных")
    submit = SubmitField("Создать аукцион")
    search = SubmitField("Поиск")


class SearchForm(FlaskForm):
    product = StringField("Название предмета", validators=[DataRequired()])
    search = SubmitField("Поиск")
    number = IntegerField("Введите порядковый номер объекта из выбранных")
    submit = SubmitField("Перейти к предмету")
