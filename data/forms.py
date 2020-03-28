from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import PasswordField, StringField, BooleanField, SubmitField
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
    submit = SubmitField("Зарегестрироваться")


class AddProductForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    description = StringField("Описание", validators=[DataRequired()])
    photo = FileField('Изображение',
                      validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField("Добавить в инвентарь")
