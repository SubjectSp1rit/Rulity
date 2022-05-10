from flask import Flask, render_template, redirect, make_response, request, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape
from data.forms import RegisterForm, LoginForm, AddGoodForm
import datetime
import sqlite3
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Integer, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return self.id

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password2):
        return check_password_hash(self.password, password2)


@app.route('/')
def index():
    data = Good.query.order_by(Good.price).all()
    return render_template('index.html', data=data)


@app.route('/purchase/<arc>/')
def purchase(arc):
    arc = int(arc)
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    res = cur.execute(f'''SELECT * FROM good WHERE id == {arc}''').fetchall()
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
        return render_template('purchase.html', arc=arc, name=name, description=description, category=category,
                               price=price, pic_url=pic_url, user_nick=user_nick, buyer_id=buyer_id, seller_id=seller_id)
    return render_template('purchase.html', arc=arc, name=name, description=description, category=category,
                           price=price, pic_url=pic_url, user_nick=user_nick)


@app.route('/delete/<arc>/')
@login_required
def delete(arc):
    arc = int(arc)
    db_sess = db_session.create_session()
    data = db_sess.query(Good).filter(Good.id == arc,
                                      Good.user_id == current_user.get_id()
                                      ).first()
    if data:
        db_sess.delete(data)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/delete_account/<arc>/')
@login_required
def delete_account(arc):
    arc = int(arc)
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.id == arc,
                                      User.id == current_user.get_id()).first()
    if data:
        db_sess.delete(data)
        db_sess.commit()
    data = db_sess.query(Good).filter(Good.user_id == arc).all()
    if data:
        for elem in data:
            db_sess.delete(elem)
            db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/edit_account/<arc>/',  methods=['GET', 'POST'])
@login_required
def edit_account(arc):
    arc = int(arc)
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        info = db_sess.query(User).filter(User.id == arc,
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
        info = db_sess.query(User).filter(User.id == arc,
                                          User.id == current_user.get_id()).first()
        if info:
            info.email = form.email.data
            info.password = form.password.data
            info.password_again = form.password_again.data
            info.name = form.name.data
            db_sess.commit()
            return redirect(f'/profile/{arc}/')
        else:
            abort(404)
    return render_template('register.html', form=form)



@app.route('/edit/<arc>/',  methods=['GET', 'POST'])
@login_required
def edit(arc):
    arc = int(arc)
    form = AddGoodForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        info = db_sess.query(Good).filter(Good.id == arc,
                                          Good.user_id == current_user.get_id()
                                          ).first()
        if info:
            form.name.data = info.name
            form.description.data = info.description
            form.category.data = info.category
            form.price.data = info.price
            form.pic_url.data = info.pic_url
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        info = db_sess.query(Good).filter(Good.id == arc,
                                          Good.user_id == current_user.get_id()
                                          ).first()
        if info:
            info.name = form.name.data
            info.description = form.description.data
            info.category = form.category.data
            info.price = form.price.data
            info.pic_url = form.pic_url.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_good.html', form=form)



@app.route('/about')
def about():
    return render_template('about.html')


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
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


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


@app.route('/add_good', methods=['GET', 'POST'])
@login_required
def add_good():
    form = AddGoodForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        good = Good(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            price=form.price.data,
            pic_url=form.pic_url.data,
            user_id=current_user.id
        )
        db_sess.add(good)
        db_sess.commit()
        return redirect('/')
    return render_template('add_good.html', form=form)


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/add', methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        price = request.form['price']

        good = Good(name=name, description=description, category=category, price=price)
        try:
            db.session.add(good)
            db.session.commit()
            return redirect('/')
        except:
            return 'ошибка'
    else:
        return render_template('add.html')

@app.route('/another')
def another():
    return render_template('another.html')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/profile/<id>/')
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
    app.run(debug=True)
