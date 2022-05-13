from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from data.forms import RegisterForm, LoginForm, AddGoodForm, SearchForm
import datetime
import sqlite3
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
UPLOAD_FOLDER = '/static/img/goods'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'KGqflOpYzMqfhmdEBFt1n6RmxKJm5uNa4WIcyj1trb9oIsiBvuUHfHwfZbXX'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# модель базы данных товаров
class Good(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    pic_url = db.Column(db.String)
    user_id = db.Column(db.Integer)

    def __repr__(self):
        return self.name


# модель базы данных пользователей
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Integer, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)
    about = db.Column(db.Text)
    cart = db.Column(db.String)
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return self.id

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password2):
        return check_password_hash(self.password, password2)


# главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        title = form.title.data.lower()
        category = form.category.data
        filtr = form.filtr.data
        if category == '☰ Каталог':
            category = None
        if filtr == 'Сортировать по':
            filtr = None
        if filtr:
            # сортировка в зависимости от выбранных значений
            if filtr == 'Цена ▲':
                if title and category:
                    data = Good.query.filter(func.lower(Good.name).contains(title),
                                             Good.category == category).order_by(Good.price).all()
                elif title and not category:
                    data = Good.query.filter(func.lower(Good.name).contains(title)).order_by(Good.price).all()
                elif category and not title:
                    data = Good.query.filter(Good.category == category).order_by(Good.price).all()
                else:
                    data = Good.query.order_by(Good.price).order_by(Good.price).all()
            if filtr == 'Цена ▼':
                if title and category:
                    data = Good.query.filter(func.lower(Good.name).contains(title),
                                             Good.category == category).order_by(Good.price.desc()).all()
                elif title and not category:
                    data = Good.query.filter(func.lower(Good.name).contains(title)).order_by(Good.price.desc()).all()
                elif category and not title:
                    data = Good.query.filter(Good.category == category).order_by(Good.price.desc()).all()
                else:
                    data = Good.query.order_by(Good.price.desc()).all()
        else:
            if title and category:
                data = Good.query.filter(func.lower(Good.name).contains(title),
                                         Good.category == category).all()
            elif title and not category:
                data = Good.query.filter(func.lower(Good.name).contains(title)).all()
            elif category and not title:
                data = Good.query.filter(Good.category == category).all()
            else:
                data = Good.query.order_by(Good.price).all()
        return render_template('index.html', data=data, form=form)
    data = Good.query.order_by(Good.price).all()
    return render_template('index.html', data=data, form=form)


# корзина пользователя
@app.route('/cart/<int:id>/')
def cart(id):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == current_user.get_id()).first()
    sp = []
    summa = 0
    if data.cart:
        splitter = map(int, data.cart.split())
        for elem in splitter:
            data2 = db_sess.query(Good).filter(Good.id == elem).first()
            sp.append([f"{data2.id}", f"{data2.name}", f"{data2.price}"])
            summa += int(data2.price)
        return render_template('cart.html', sp=sp, summa=summa)
    return render_template('cart.html', message='Ваша корзина пуста :(')


# удаление товара из корзины пользователя
@app.route('/delete_from_cart/<int:id>/')
def delete_from_cart(id):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == current_user.get_id()).first()
    if data.cart:
        new_cart = ''
        cart = data.cart.split()
        for elem in cart:
            if int(elem) == id:
                continue
            else:
                new_cart += str(elem)
        new_cart = ' '.join(list(new_cart))
        data.cart = new_cart
        db_sess.commit()
    return redirect(f'/cart/{current_user.get_id()}/')



# удаление всез товаров из корзины
@app.route('/clear_cart/<int:id>/')
def clear_cart(id):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == current_user.get_id(),
                                      User.id == id).first()
    if data.cart:
        data.cart = None
        db_sess.commit()
    return redirect(f'/cart/{id}/')


# подробная страница с товаром
@app.route('/purchase/<int:id>/')
def purchase(id):
    # ниже код - полный колхоз, который был написан в первый день создания проекта и я не знаю
    # что может быть уродливее этого. Но оно же работает, right? :D
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    res = cur.execute(f'''SELECT * FROM good WHERE id == {id}''').fetchall()
    name = res[0][1]
    description = res[0][2]
    category = res[0][3]
    price = res[0][4]
    pic_url = res[0][5]
    result = cur.execute(f'''SELECT * FROM user WHERE id == {res[0][6]}''').fetchall()
    user_nick = result[0][3]
    if current_user.is_authenticated:
        seller_id = int(result[0][0])
        buyer_id = int(current_user.get_id())
        return render_template('purchase.html', arc=id, name=name, description=description, category=category,
                               price=price, pic_url=pic_url, user_nick=user_nick, buyer_id=buyer_id, seller_id=seller_id)
    return render_template('purchase.html', arc=id, name=name, description=description, category=category,
                           price=price, pic_url=pic_url, user_nick=user_nick)


# добавление товара в корзину
@app.route('/add_to_cart/<int:id>/')
def add_to_cart(id):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == current_user.get_id()).first()
    if data:
        if data.cart:
            data.cart = data.cart + ' ' + str(id)
        else:
            data.cart = str(id)
        db_sess.commit()
    return redirect(f'/purchase/{id}/')


# удаление товара
@app.route('/delete/<int:id>/')
@login_required
def delete(id):
    db_sess = db_session.create_session()
    data = db_sess.query(Good).filter(Good.id == id,
                                      Good.user_id == current_user.get_id()
                                      ).first()
    if data:
        if data.pic_url != 'nophoto.jpg':
            os.remove(f'static/img/goods/{data.pic_url}')
        db_sess.delete(data)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


# удаление аккаунта
@app.route('/delete_account/<int:id>/')
@login_required
def delete_account(id):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == id,
                                      User.id == current_user.get_id()).first()
    if data:
        db_sess.delete(data)
        db_sess.commit()
    data = db_sess.query(Good).filter(Good.user_id == id).all()
    if data:
        for elem in data:
            if elem.pic_url != 'nophoto.jpg':
                os.remove(f'static/img/goods/{elem.pic_url}')
            db_sess.delete(elem)
            db_sess.commit()
    else:
        abort(404)
    return redirect('/')


# изменение данных аккаунта
@app.route('/edit_account/<int:id>/', methods=['GET', 'POST'])
@login_required
def edit_account(id):
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        info = db_sess.query(User).filter(User.id == id,
                                          User.id == current_user.get_id()).first()
        if info:
            form.email.data = info.email
            form.password.data = None
            form.password_again.data = None
            form.name.data = info.name
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        info = db_sess.query(User).filter(User.id == id,
                                          User.id == current_user.get_id()).first()
        if info:
            info.email = form.email.data
            info.password = generate_password_hash(form.password.data)
            info.password_again = form.password_again.data
            info.name = form.name.data
            db_sess.commit()
            return redirect(f'/profile/{id}/')
        else:
            abort(404)
    return render_template('register.html', form=form)


# изменение данных товара
@app.route('/edit/<int:id>/',  methods=['GET', 'POST'])
@login_required
def edit(id):
    form = AddGoodForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        info = db_sess.query(Good).filter(Good.id == id,
                                          Good.user_id == current_user.get_id()
                                          ).first()
        if info:
            form.name.data = info.name
            form.description.data = info.description
            form.category.data = info.category
            form.price.data = info.price
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        info = db_sess.query(Good).filter(Good.id == id,
                                          Good.user_id == current_user.get_id()
                                          ).first()
        if info:
            info.name = form.name.data
            info.description = form.description.data
            info.category = form.category.data
            info.price = form.price.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_good.html', form=form, msg='Изменить изображение нельзя.')



# описание проекта Rulity
@app.route('/about')
def about():
    return render_template('about.html')

# регистрация нового пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html',
                                   form=form,
                                   message="Пользователь с такой почтой уже существует")
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html',
                                   form=form,
                                   message="Пользователь с таким ником уже существует")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


# авторизация пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            print('ВХОД ВЫПОЛНЕН УСПЕШНО!')
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# добавление нового товара
@app.route('/add_good', methods=['GET', 'POST'])
@login_required
def add_good():
    form = AddGoodForm()
    if form.validate_on_submit():
        exceptions = ['jpg', 'png', 'raw', 'jpeg', 'tiff', 'gif', 'psd', 'bmp']
        file = request.files['file']
        filename = file.filename
        if filename.split('.')[1].lower() not in exceptions:
            filename = 'nophoto.jpg'
        else:
            try:
                img = file.read()
                with open(f'static/img/goods/{filename}', 'wb') as f:
                    f.write(img)
            except FileNotFoundError:
                filename = 'nophoto.jpg'

        db_sess = db_session.create_session()
        good = Good(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            price=form.price.data,
            pic_url=filename,
            user_id=current_user.id
        )

        db_sess.add(good)
        db_sess.commit()

        return redirect('/')
    return render_template('add_good.html', form=form)


# часто задаваемые вопросы касательно работы сайты
@app.route('/faq')
def faq():
    return render_template('faq.html')


# страница для "пустых" кнопок))
@app.route('/another')
def another():
    return render_template('another.html')


# загрузка текущего пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# выход из аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# профиль текущего пользователя
@app.route('/profile/<int:id>/')
def profile(id):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == id).first()
    if not data:
        abort(404)
    created_date = data.created_date.strftime("%D")
    if current_user.is_authenticated:
        cur_user_id = int(current_user.get_id())
        profile_id = int(data.id)
        return render_template('profile.html', profile_id=profile_id, cur_user_id=cur_user_id, name=data.name, created_date=created_date, mail=data.email)
    profile_id = int(data.id)
    return render_template('profile.html', profile_id=profile_id, name=data.name,
                           created_date=created_date)


if __name__ == "__main__":
    db_session.global_init("database.db")
    app.run()
