from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    in_work = db.Column(db.Boolean, nullable=False)


    def __repr__(self):
        return '<User: %r, %r, %r, %r, %r, %r, %r' % self.id % self.username % self.email % self.first_name % \
               self.last_name % self.password % self.in_work


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    manufacturer = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Product: %r, %r, %r, %r>' % self.id % self.name % self.manufacturer % self.quantity


class WorkTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_first_name = db.Column(db.Integer, db.ForeignKey('user.first_name'), nullable=False)
    employee_last_name = db.Column(db.Integer, db.ForeignKey('user.last_name'), nullable=False)
    current_time = db.Column(db.DateTime, nullable=False)
    in_work = db.Column(db.Boolean, db.ForeignKey('user.in_work'), nullable=False)


# class EndTime(db.Model):
#     id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
#     employee_first_name = db.Column(db.Integer, db.ForeignKey('user.first_name'), nullable=False)
#     employee_last_name = db.Column(db.Integer, db.ForeignKey('user.last_name'), nullable=False)
#     end_time = db.Column(db.DateTime, nullable=False)


# Page Routing
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        new_username = request.form['username-input']
        new_password = request.form['password-input']

        try:
            name_found = False
            password_found = False
            users = User.query.order_by(User.id).all()
            for user in users:
                if new_username == user.username:
                    name_found = True
                    if new_password == user.password:
                        password_found_found = True
                        return redirect('/profile')
                    else:
                        return 'Wrong password'
                else:
                    return 'User not exist'

        except:
            return 'Error'

    return render_template('/user_management/login.html')


@app.route('/new_user', methods=['POST', 'GET'])
def new_user():
    if request.method == 'POST':
        new_id = request.form['id-input']
        new_username = request.form['username-input']
        new_email = request.form['email-input']
        new_first_name = request.form['first-name-input']
        new_last_name = request.form['last-name-input']
        new_password = request.form['password-input']
        new_user_obj = User(id=new_id, username=new_username, email=new_email, first_name=new_first_name,
                            last_name=new_last_name, password=new_password, in_work=False)

        try:
            db.session.add(new_user_obj)
            db.session.commit()
            return redirect('/profile')
        except:
            print(new_user_obj.first_name)
            users = User.query.order_by(User.id).all()
            print(users)
            return 'There was an issue adding the new user: '

    return render_template('/user_management/new_user.html')


@app.route('/forgot_password')
def forgot_password():
    return render_template('/user_management/forgot_password.html')


@app.route('/manage', methods=['POST', 'GET'])
def manage():
    if request.method == 'POST':
        new_id = request.form['id-input']
        new_name = request.form['name-input']
        new_manufacturer = request.form['manufacturer-input']
        new_quantity = request.form['quantity-input']
        new_item = Product(id=new_id, name=new_name, manufacturer=new_manufacturer, quantity=new_quantity)

        try:
            db.session.add(new_item)
            db.session.commit()
            return redirect('/manage')
        except:
            return 'There was an issue adding your product'

    else:
        products = Product.query.order_by(Product.id).all()
        return render_template('/product_management/manage.html', products=products)


@app.route('/manage/delete/<int:id>')
def delete(id):
    product_to_delete = Product.query.get_or_404(id)

    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return redirect('/manage')
    except:
        return 'There was a problem deleting that product'


@app.route('/manage/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.id = request.form['id-input']
        product.name = request.form['name-input']
        product.manufacturer = request.form['manufacturer-input']
        product.quantity = request.form['quantity-input']

        try:
            db.session.commit()
            return redirect('/manage')
        except:
            return 'There was an issue updating your task'

    else:
        return render_template('product_management/update.html', product=product)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/profile', )
def profile():
    users = User.query.order_by(User.id).all()
    return render_template('/user_management/profile.html', user_list=users)


@app.route('/overview')
def overview():
    return render_template('overview.html')


@app.route('/time', methods=['POST', 'GET'])
def time():
    if request.method == 'POST':
        t = datetime.datetime.now().replace(microsecond=0)
        user_id = request.form['id-input']

        user = User.query.get_or_404(user_id)
        if user.in_work:
            print("True")
            user.in_work = False
            new_time = WorkTime(employee_first_name=user.first_name, employee_last_name=user.last_name, current_time=t,
                                in_work=user.in_work)
            db.session.add(new_time)
        else:
            print("False")
            user.in_work = True
            new_time = WorkTime(employee_first_name=user.first_name, employee_last_name=user.last_name, current_time=t,
                                in_work=user.in_work)
            db.session.add(new_time)
            print(f'Time: {new_time.current_time}')
        print(f'User: {user.in_work}')
        try:
            db.session.commit()
            print("Commited")
        except:
            print("Not commited")
    work_times = WorkTime.query.order_by(WorkTime.current_time).all()
    return render_template('time/time.html', work_times=work_times)


if __name__ == "__main__":
    app.run(debug=True)