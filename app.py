from flask import Flask, render_template, request, redirect, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import barcode

# importing flask admin lib
from flask_admin import Admin, BaseView, expose
# Allows admin page to view models
from flask_admin.contrib.sqla import ModelView
# Allows for login authentication
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# changed id column to Integer
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<User: %r, %r>' % self.id % self.username


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    manufacturer = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # barcode is an added property that uses big integer
    # to store over 12 digits (minimum needed for the
    # barcode I selected
    barcode = db.Column(db.BigInteger)

    def __repr__(self):
        return '<Product: %r, %r, %r, %r>' % self.id % self.name % self.manufacturer % self.quantity % self.barcode


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
        new_user = User(id=new_id, username=new_username, email=new_email, first_name=new_first_name
                        , last_name=new_last_name, password=new_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/profile')
        except:
            print(new_user.first_name)
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
        # Use the primary unique ID to make unique barcodes
        b = int(new_id) + 100000000000
        # Set the new product barcode to the b variable above
        new_item = Product(id=new_id, name=new_name, manufacturer=new_manufacturer
                           , quantity=new_quantity, barcode=b)
        # Uses the ean13 barcode format to incorporate the b variable
        ean = barcode.get('ean13', str(b))
        # Optional print statement to see process
        print(f'code: {ean.get_fullcode()}')
        # The file is saved by using the unique primary ID of
        # the product to easily obtain the file
        filename = ean.save(new_id)
        # Optional print statement
        print(f'filename: {filename}')

        try:
            db.session.add(new_item)
            db.session.commit()
            return redirect('/manage')
        except:
            return 'There was an issue adding your product'

    else:
        products = Product.query.order_by(Product.id).all()
        return render_template('/product_management/manage.html', products=products)


# New URL for Barcode branch
@app.route('/manage/download/<int:id>', methods=['GET', 'POST'])
def download(id):
    # Uses the product unique primary ID to locate the file
    file_name = str(id) + '.svg'
    # Returns the .svg file of the barcode
    # you can do that {} method and store it in a file, figure out how to put it in a file first
    return send_file(file_name)


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

        # added barcode func
        product.barcode = request.form['barcode-input']

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


# displays the calendar page
# calendar uses the "full calendar" api
@app.route('/calendar')
def calendar():
    return render_template("calendar.html")


# This is used so that users can input events into the calender using the 'events.json'
# It can be adjusted to query data from a db in the next iteration if requested
@app.route('/data')
def return_data():
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')

    with open("events.json", "r") as input_data:

        return input_data.read()


# Admin Access code
# Redirects back to the homepage of the website
class HomepageRedirect(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')


# Redirects to login authentication
class AdminLogin(BaseView):
    @expose('/')
    def admin_login(self):
        user = User.query.get({"id": 1})
        login_user(user)
        return self.render('admin_management/admin_login.html')


# Redirects to logout authentication
class AdminLogout(BaseView):
    @expose('/')
    def admin_logout(self):
        logout_user()
        return self.render('admin_management/admin_logout.html')


# set optional bootswatch theme
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SECRET_KEY'] = 'mysecret'

login = LoginManager(app)


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# this creates a model class for the User Table
class UserModel(ModelView):
    # makes it so that it is accessible/not based on a condition
    def is_accessible(self):
        return current_user.is_authenticated


# this allows a specific admin page to be accessed through /admin
admin = Admin(app)
# Add administrative views here
admin.add_view(UserModel(User, db.session))
admin.add_view(AdminLogin(name="Login"))
admin.add_view(AdminLogout(name="Logout"))
admin.add_view(HomepageRedirect(name="Return to Homepage"))


'''
@app.route('/admin-login')
def admin_login():
    user = User.query.get({"id": 1})
    login_user(user)
    return "Admin Logged In"

'''
'''
@app.route('/admin-logout')
def admin_logout():
    logout_user()
    return "Admin Logged out"
'''


if __name__ == "__main__":
    app.run(debug=True)