from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class AddGoodForm(FlaskForm):
    name = StringField('Название товара', validators=[DataRequired()])
    description = TextAreaField('Описание товара', validators=[DataRequired()])
    category = SelectField('Категория товара', choices=[('Еда'),
                                                        ('Бытовая техника'),
                                                        ('Электроника'),
                                                        ('Косметика'),
                                                        ('Одежда'),
                                                        ('Мебель')])
    price = IntegerField('Цена товара', validators=[DataRequired()])
    pic_url = StringField('URL-ссылка на изображение')
    submit = SubmitField('Подтвердить')
