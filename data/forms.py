from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired


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
    photo = FileField("Фотография")
    submit = SubmitField("Зарегестрироваться")
