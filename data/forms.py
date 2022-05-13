from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired, ValidationError


def lencheck(form, field):
    if len(field.data) > 1080:
        raise ValidationError('Поле должно быть меньше 1080 символов')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Подтвердить')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class AddGoodForm(FlaskForm):
    name = StringField('Название товара', validators=[DataRequired()])
    description = TextAreaField('Описание товара', validators=[DataRequired(), lencheck])
    category = SelectField('Категория товара', choices=[('Еда'),
                                                        ('Бытовая техника'),
                                                        ('Электроника'),
                                                        ('Косметика'),
                                                        ('Одежда'),
                                                        ('Мебель'),
                                                        ('Другое')])
    price = IntegerField('Цена товара', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')


class SearchForm(FlaskForm):
    title = StringField('')
    category = SelectField('Категория', choices=[('☰ Каталог'),
                                                 ('Еда'),
                                                 ('Бытовая техника'),
                                                 ('Электроника'),
                                                 ('Косметика'),
                                                 ('Одежда'),
                                                 ('Мебель'),
                                                 ('Другое')])
    filtr = SelectField('Категория', choices=[('Сортировать по'),
                                                 ('Цена ▲'),
                                                 ('Цена ▼')])
    submit = SubmitField('Поиск')
