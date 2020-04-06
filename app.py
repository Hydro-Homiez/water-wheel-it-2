import datetime

from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "super secret key"
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
    in_work = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<User-id: ' + self.id + ', username: ' + self.username + ', email: ' + self.email + ', first name: ' + \
                self.first_name + ', last name: ' + self.last_name + ', password: ' + self.password + ', in work: ' + \
                self.in_work + ', location: ' + self.location + '>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    manufacturer = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Product-id: ' + self.id + ', name: ' + self.name + ', manufacturer: ' + self.manufacturer + ', quantity: ' \
               + self.quantity + '>'


class WorkTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_first_name = db.Column(db.Integer, db.ForeignKey('user.first_name'), nullable=False)
    employee_last_name = db.Column(db.Integer, db.ForeignKey('user.last_name'), nullable=False)
    current_time = db.Column(db.DateTime, nullable=False)
    in_work = db.Column(db.Boolean, db.ForeignKey('user.in_work'), nullable=False)


# Page Routing
# Single Page Navigation
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/profile', )
def profile():
    users = User.query.order_by(User.id).all()
    return render_template('/user_management/profile.html', user_list=users)


@app.route('/time', methods=['POST', 'GET'])
def time():
    if request.method == 'POST':
        t = datetime.datetime.now().replace(microsecond=0)
        user_id = request.form['id-input']

        user = User.query.get_or_404(user_id)
        if user.in_work:
            user.in_work = False
        else:
            user.in_work = True
        new_time = WorkTime(employee_first_name=user.first_name, employee_last_name=user.last_name, employee_id=user.id,
                            current_time=t, in_work=user.in_work)
        db.session.add(new_time)
        try:
            db.session.commit()
        except:
            return render_template('reusable_components/error.html', page='Clock-in',
                                   error_message='Time not committed')
    work_times = WorkTime.query.order_by(WorkTime.current_time).all()
    return render_template('time/time.html', work_times=work_times)


# User Management Navigation
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        new_username = request.form['username-input']
        new_password = request.form['password-input']

        try:
            users = User.query.order_by(User.id).all()
            for user in users:
                if new_username == user.username:
                    if new_password == user.password:
                        session['user_location'] = user.location
                        return redirect('/login_success')
                    else:
                        return render_template('reusable_components/error.html', page='Login',
                                               error_message='Wrong Password')
        except:
            return render_template('reusable_components/error.html', page='Login',
                                   error_message='User does not exist')

    return render_template('/user_management/login.html')

@app.route('/logout')
def logout():
    session.pop('user_location', None)
    return redirect('/login')

@app.route('/new_user', methods=['POST', 'GET'])
def new_user():
    if request.method == 'POST':
        new_id = request.form['id-input']
        new_username = request.form['username-input']
        new_email = request.form['email-input']
        new_first_name = request.form['first-name-input']
        new_last_name = request.form['last-name-input']
        new_password = request.form['password-input']
        new_location = request.form['location-input']
        user = User(id=new_id, username=new_username, email=new_email, first_name=new_first_name,
                    last_name=new_last_name, password=new_password, location=new_location)

        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/profile')
        except:
            return render_template('reusable_components/error.html', page='Insertion',
                                   error_message='There was an issue adding the new user ')

    return render_template('/user_management/new_user.html')


@app.route('/login_success')
def login_success():
    return render_template('/user_management/login_success.html')


@app.route('/login_fail')
def login_fail():
    return render_template('/user_management/login_fail.html')


# Product Management Navigation
@app.route('/manage', methods=['POST', 'GET'])
def manage():
    work_location = session.get('user_location', 'N/A')
    if request.method == 'POST':
        new_id = request.form['id-input']
        new_name = request.form['name-input']
        new_manufacturer = request.form['manufacturer-input']
        new_category = request.form['category-input']
        new_quantity = request.form['quantity-input']
        new_item = Product(id=new_id, name=new_name, manufacturer=new_manufacturer, category=new_category,
                           quantity=new_quantity, location=work_location)
        print(new_item.location)
        try:
            db.session.add(new_item)
            db.session.commit()
            return redirect('/manage')
        except:
            return render_template('reusable_components/error.html', page='Insertion',
                                   error_message='There was an issue adding your product')

    else:
        products = Product.query.filter_by(location=work_location).order_by(Product.id).all()
        return render_template('/product_management/manage.html', products=products)


@app.route('/manage/delete/<int:id>')
def delete(id):
    product_to_delete = Product.query.get_or_404(id)

    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return redirect('/manage')
    except:
        return render_template('reusable_components/error.html', page='Deletion',
                               error_message='There was a problem deleting that product')


@app.route('/manage/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    product = Product.query.get_or_404(id)
    print(f'product {product.name}')

    if request.method == 'POST':
        product.name = request.form['name-input']
        product.manufacturer = request.form['manufacturer-input']
        product.category = request.form['category-input']
        product.quantity = request.form['quantity-input']

        try:
            db.session.commit()
            return redirect('/manage')
        except:
            return render_template('reusable_components/error.html', page='Update',
                                   error_message='There was an issue updating your task')

    else:
        return render_template('product_management/update.html', product=product)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search-input']
        if search_query == "":
            return render_template('reusable_components/error.html', page='Search',
                                   error_message='Make sure to fill in the search bar.')
        temp_results = Product.query.filter(Product.name.contains(search_query)).all()
        temp_results += Product.query.filter(Product.manufacturer.contains(search_query)).all()
        temp_results += Product.query.filter(Product.category.contains(search_query)).all()
        search_results = []
        for t in temp_results:
            if t not in search_results:
                search_results.append(t)
    return render_template('product_management/search_results_table.html', search_results=search_results)


if __name__ == "__main__":
    app.run(debug=True)
