from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, session, Response
import datetime


from flask_sqlalchemy import SQLAlchemy
import json
import barcode

# importing flask admin lib
from flask_admin import Admin, BaseView, expose
# Allows admin page to view models
from flask_admin.contrib.sqla import ModelView
# Allows for login authentication
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user

import datetime

import os

# for export feature import these
import csv

from sqlalchemy import desc

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    in_work = db.Column(db.Boolean, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    admin = db.Column(db.Boolean, default=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    manufacturer = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    barcode = db.Column(db.BigInteger)
    notify_minimum = db.Column(db.Integer)
    image_name = db.Column(db.String(200), nullable=False)
    image_type = db.Column(db.String(200), nullable=False)


class WorkTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_first_name = db.Column(db.Integer, db.ForeignKey('user.first_name'), nullable=False)
    employee_last_name = db.Column(db.Integer, db.ForeignKey('user.last_name'), nullable=False)
    current_time = db.Column(db.DateTime, nullable=False)
    in_work = db.Column(db.Boolean, db.ForeignKey('user.in_work'), nullable=False)


class ActionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    employee_first_name = db.Column(db.String, db.ForeignKey('user.first_name'))
    employee_last_name = db.Column(db.String, db.ForeignKey('user.last_name'))
    action = db.Column(db.String(200), nullable=False)
    current_time = db.Column(db.DateTime, nullable=False)


class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start = db.Column(db.String(200), nullable=False)
    all_day = db.Column(db.Boolean, default=True)

    @property
    def serialized(self):
        return {
            'title': self.title,
            'start': self.start,
            'allDay': self.all_day
        }


# Page Routing
# Single Page Navigation
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/profile')
def profile():
    users = User.query.order_by(User.id).all()
    return render_template('/user_management/profile.html', user_list=users)


# Clock-in system
@app.route('/time', methods=['POST', 'GET'])
def time():
    if request.method == 'POST':
        t = datetime.datetime.now().replace(microsecond=0)
        user_id = session['user_id']

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
            session['in_work'] = user.in_work
        except:
            return render_template('reuseable_components/error.html', page='Clock-in',
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
                        session['user_id'] = user.id
                        session['user_first_name'] = user.first_name
                        session['user_last_name'] = user.last_name
                        session['user_location'] = user.location
                        session['user_admin'] = user.admin
                        session['in_work'] = user.in_work
                        return redirect('/login_success')
                    else:
                        return render_template('reuseable_components/error.html', page='Login',
                                               error_message='Wrong Password')
        except:
            return render_template('reuseable_components/error.html', page='Login',
                                   error_message='User does not exist')

    return render_template('/user_management/login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_first_name', None)
    session.pop('user_last_name', None)
    session.pop('user_location', None)
    session.pop('user_admin', None)
    return render_template('/user_management/logout.html')


@app.route('/new_user', methods=['POST', 'GET'])
def new_user():
    if request.method == 'POST':
        new_id = request.form.get('id-input', None)
        new_username = request.form.get('username-input', None)
        new_email = request.form.get('email-input', None)
        new_first_name = request.form.get('first-name-input', None)
        new_last_name = request.form.get('last-name-input', None)
        new_password = request.form.get('password-input', None)
        new_location = request.form.get('location-input', None)
        if new_id is None or new_username is None or new_email is None or new_first_name is None or \
                new_last_name is None or new_password is None or new_location is None:
            return render_template('reuseable_components/error.html', page='Insertion',
                                   error_message='There was an issue updating your task')

        # checks if the admin code is correct to flag as admin, default code is set to 'admin'
        new_admin = request.form.get('admin-input')
        if new_admin == 'admin':
            new_admin = 1
        else:
            new_admin = 0

        try:
            new_user = User(id=new_id, username=new_username, email=new_email, first_name=new_first_name,
                            last_name=new_last_name, password=new_password, location=new_location, in_work=False,
                            admin=new_admin)
            db.session.add(new_user)
            db.session.commit()
            # changed from redirect /profile to /login
            return redirect('/login')
        except:
            return render_template('reuseable_components/error.html', page='Insertion',
                                   error_message='There was an issue adding the new user ')

    return render_template('/user_management/new_user.html')


@app.route('/login_success')
def login_success():
    return render_template('/user_management/login_success.html')


@app.route('/login_fail')
def login_fail():
    return render_template('/user_management/login_fail.html')


# Product Mangement Navigation
@app.route('/manage', methods=['POST', 'GET'])
def manage():
    session.pop('low_stock', None)
    current_time = datetime.datetime.now().replace(microsecond=0)
    employee_id = session.get('user_id', 'N/A')
    first_name = session.get('user_first_name', 'N/A')
    last_name = session.get('user_last_name', 'N/A')
    work_location = session.get('user_location', 'N/A')
    if request.method == 'POST':
        new_id = request.form.get('id-input', None)
        new_name = request.form.get('name-input', None)
        new_manufacturer = request.form.get('manufacturer-input', None)
        new_category = request.form.get('category-input', None)
        new_quantity = request.form.get('quantity-input', None)
        new_image = ''
        if 'files' in request.files:
            folder_name = os.path.join(APP_ROOT, 'static\\images\\products')
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            uploaded_files = request.files.get('files')
            file_name = uploaded_files.filename
            if file_name == '':
                new_image = ''
                image_type = ''
            else:
                extension = file_name[file_name.index('.'):len(file_name)]
                image_type = extension
                if extension == '.png' or extension == '.jpg':
                    file_name = f'{new_id}_{new_name}{extension}'
                    destination = "\\".join([folder_name, file_name])
                    uploaded_files.save(destination)
                    new_image = file_name
                else:
                    return render_template('reuseable_components/error.html', page='Insertion',
                                           error_message='The supported file types are .png and .jpg.')
        if new_id is None or new_name is None or new_manufacturer is None or new_category is None or \
                new_quantity is None:
            return render_template('reuseable_components/error.html', page='Insertion',
                                   error_message='Make sure to fill the ID, name, manufacturer, category, and quantity '
                                                 'inputs.')
        if request.form['notify-input'] == '':
            new_minimum = round(int(new_quantity) * .1)
        else:
            new_minimum = request.form.get('notify-input')
        b = int(new_id) + 100000000000
        ean = barcode.get('ean13', str(b))
        folder_name = os.path.join(APP_ROOT, 'static\\images\\barcodes')
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        file_name = f'{new_id}'
        destination = "\\".join([folder_name, file_name])
        ean.save(destination)

        try:
            new_item = Product(id=new_id, name=new_name, manufacturer=new_manufacturer, category=new_category,
                               quantity=new_quantity, location=work_location, barcode=b, notify_minimum=new_minimum,
                               image_name=new_image, image_type=image_type)
            action = f'Added product: {new_id} {new_name}'
            action_record = ActionRecord(employee_id=employee_id, employee_first_name=first_name,
                                         employee_last_name=last_name, action=action,
                                         current_time=current_time)
            db.session.add(new_item)
            db.session.add(action_record)
            db.session.commit()
            return redirect('/manage')
        except:
            return render_template('reuseable_components/error.html', page='Insertion',
                                   error_message='There was an issue adding your product. '
                                                 'Make sure you are logged in modifiying products, and check if the '
                                                 'product already exists. ')
    else:
        products = Product.query.filter_by(location=work_location).order_by(Product.id).all()
        low_stock = []
        for p in products:
            if p.quantity < p.notify_minimum:
                low_stock.append(p.name)
        session['low_stock'] = low_stock
        return render_template('/product_management/manage.html', products=products)


# New URL for Barcode branch
@app.route('/manage/download/<int:id>', methods=['GET', 'POST'])
def download(id):
    folder_name = os.path.join(APP_ROOT, 'static\\images\\barcodes')
    file_name = str(id) + '.svg'
    return send_from_directory(folder_name, file_name, as_attachment=True)


@app.route('/manage/delete/<int:id>')
def delete(id):
    current_time = datetime.datetime.now().replace(microsecond=0)
    employee_id = session.get('user_id', 'N/A')
    first_name = session.get('user_first_name', 'N/A')
    last_name = session.get('user_last_name', 'N/A')
    product_to_delete = Product.query.get_or_404(id)
    action = f'Deleted product: {product_to_delete.id} {product_to_delete}'
    action_record = ActionRecord(employee_id=employee_id, employee_first_name=first_name, employee_last_name=last_name,
                                 action=action, current_time=current_time)
    try:
        db.session.delete(product_to_delete)
        db.session.add(action_record)
        db.session.commit()
        return redirect('/manage')
    except:
        return render_template('reuseable_components/error.html', page='Deletion',
                               error_message='There was a problem deleting that product')


@app.route('/manage/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    current_time = datetime.datetime.now().replace(microsecond=0)
    employee_id = session.get('user_id', 'N/A')
    first_name = session.get('user_first_name', 'N/A')
    last_name = session.get('user_last_name', 'N/A')
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        new_name = request.form.get('name-input', None)
        new_manufacturer = request.form.get('manufacturer-input', None)
        new_quantity = request.form.get('quantity-input', None)
        if new_name is None or new_manufacturer is None or new_quantity is None:
            return render_template('reuseable_components/error.html', page='Insertion',
                                   error_message='There was an issue adding your product')
        product.name = new_name
        product.manufacturer = new_manufacturer
        product.quantity = new_quantity
        action = f'Updated product: {product.id} {new_name}'
        action_record = ActionRecord(employee_id=employee_id, employee_first_name=first_name,
                                     employee_last_name=last_name, action=action, current_time=current_time)
        if 'files' in request.files:
            folder_name = os.path.join(APP_ROOT, 'static\\images\\products')
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            else:
                uploaded_files = request.files.get('files')
                file_name = uploaded_files.filename
                if file_name == '':
                    pass
                else:
                    extension = file_name[file_name.index('.'):len(file_name)]
                    product.image_type = extension
                    if extension == '.png' or extension == '.jpg':
                        file_name = f'{id}_{new_name}{extension}'
                        destination = "\\".join([folder_name, file_name])
                        uploaded_files.save(destination)
                        product.image_name = file_name
                    else:
                        return render_template('reuseable_components/error.html', page='Insertion',
                                               error_message='The supported file types are .png and .jpg.')
                if new_name is None or new_manufacturer is None or new_quantity is None:
                    return render_template('reuseable_components/error.html', page='Insertion',
                                           error_message='Make sure to fill the name, manufacturer, category, and quantity '
                                                         'inputs.')
                try:
                    db.session.add(action_record)
                    db.session.commit()
                    return redirect('/manage')
                except:
                    return render_template('reuseable_components/error.html', page='Update',
                                           error_message='There was an issue updating your task')
    else:
        return render_template('product_management/update.html', product=product)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search-input']
        if search_query == "":
            return render_template('reuseable_components/error.html', page='Search',
                                   error_message='Make sure to fill in the search bar.')
        temp_results = Product.query.filter(Product.name.contains(search_query)).all()
        temp_results += Product.query.filter(Product.manufacturer.contains(search_query)).all()
        search_results = []
        for t in temp_results:
            if t not in search_results:
                search_results.append(t)
    return render_template('product_management/search_results_table.html', search_results=search_results)


@app.route('/search_category', methods=['GET', 'POST'])
def search_category():
    if request.method == 'POST':
        search_query = request.form['search-category-input']
        if search_query == "":
            return render_template('reuseable_components/error.html', page='Search',
                                   error_message='Make sure to fill in the search bar.')
        temp_results = Product.query.filter(Product.category.contains(search_query)).all()
        search_results = []
        for t in temp_results:
            if t not in search_results:
                search_results.append(t)
    return render_template('product_management/search_results_table.html', search_results=search_results)


# displays the calendar page
# calendar uses the "full calendar" api
@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if request.method == 'POST':
        print('working')
        print(request.json)
        title = request.json['title']
        start = request.json['start']
        all_day = request.json['allDay']
        print(title)
        calendar_event = CalendarEvent(title=title, start=start, all_day=all_day)
        print(calendar_event)
        try:
            db.session.add(calendar_event)
            db.session.commit()
            print('saved')
        except:
            return render_template('reuseable_components/error.html', page='Calendar',
                                   error_message='There was an issue adding the event.')
    return render_template("calendar.html")


@app.route('/calendar_edit')
def calendar_edit():
    events = CalendarEvent.query.all()
    print(events)
    if len(events) > 0:
        print('more than one')
    return render_template("calendar_edit.html", events=events)


@app.route('/calendar_data')
def calendar_data():
    events = CalendarEvent.query.all()
    if len(events) > 0:
        date = []
        for e in events:
            date.append(e.serialized)
        response = jsonify(date)
        print(response.data)
        return response
    return


# Graphs page
@app.route('/graphs')
def graphs():
    work_location = session.get('user_location', 'N/A')
    products = Product.query.filter_by(location=work_location).order_by(Product.quantity).all()
    return render_template("graphs.html", products=products)


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
    # The User Model is only accessible if the admin is logged in and authenticated
    def is_accessible(self):
        return current_user.is_authenticated


# this allows a specific admin page to be accessed through /admin
admin = Admin(app)
# Add administrative views here
admin.add_view(UserModel(User, db.session))
# admin.add_view(AdminLogin(name="Login"))
admin.add_view(AdminLogout(name="Logout"))
admin.add_view(HomepageRedirect(name="Return to Homepage"))


# Admin must login in order to view the page, admin is authenticated upon successful login
@app.route('/admin-login', methods=['POST', 'GET'])
def admin_login():
    current_time = datetime.datetime.now().replace(microsecond=0)
    employee_id = session.get('user_id', 'N/A')
    first_name = session.get('user_first_name', 'N/A')
    last_name = session.get('user_last_name', 'N/A')
    if current_user.is_authenticated is True:
        return redirect('/admin')
    elif request.method == 'POST':
        new_username = request.form['username-input']
        new_password = request.form['password-input']

        try:
            name_found = False
            password_found = False
            admin_found = False
            users = User.query.order_by(User.id).all()
            for user in users:
                if new_username == user.username:
                    name_found = True
                    if new_password == user.password:
                        password_found = True
                        if user.admin is True:
                            action_record = ActionRecord(employee_id=employee_id, employee_first_name=first_name,
                                                         employee_last_name=last_name,
                                                         action="Accessed admin page", current_time=current_time)
                            db.session.add(action_record)
                            db.session.commit()
                            login_user(user)
                            return redirect('/admin')
                        else:
                            return 'Access Denied, User not Admin'
                    else:
                        return 'Wrong password'
                # This is commented out because the loop automatically terminates if the first user isn't found.
                # else:
                    # return 'Admin does not exist'
        except:
            return "Error please contact Management"
    return render_template('/admin_management/admin_login.html')

  
# Activity Records
@app.route('/activity', methods=['GET'])
def activity_records():
    is_admin = session.get('user_admin', 'N/A')
    if is_admin:
        records = ActionRecord.query.order_by(desc(ActionRecord.current_time)).all()
        return render_template("activity_record.html", activity_records=records)
    else:
        return render_template('reuseable_components/error.html', page='Activity Record',
                               error_message='Only admins can access this page.')
      
      
# To export table to csv format
@app.route('/export', methods=['GET'])
def export():

    # header row for csv file
    prod_list = [['id', 'name', 'manufacturer', 'category', 'quantity', 'location', 'barcode']]

    # grab all table contents
    prod = Product.query.all()

    # add the contents to a list
    for each in prod:
        prod_list.append([each.id, each.name, each.manufacturer,
                          each.category, each.quantity, each.location, each.barcode])

    # add a newline for every new row
    prod_list = '\n'.join([','.join(map(str, item)) for item in prod_list])
    prod_list = str(prod_list)

    csv = prod_list

    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=product_data.csv"}
    )


if __name__ == "__main__":
    app.run(debug=True)
