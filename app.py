from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, make_response
from sqlalchemy import create_engine, or_, and_, func
from sqlalchemy.orm import sessionmaker, joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import User, Login, Property, Base, db
from functools import wraps
import smtplib
from email.message import EmailMessage
from string import Template
from pathlib import Path

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:SQLPassX&7@localhost/click_and_buy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

db.init_app(app)


@app.template_filter('format_currency')
def format_currency(value):
    return f'R {value:,.2f}'


def generate_pagination_html(total_pages, current_page):
    pagination_html = '<ul class="pagination pagination-links justify-content-center">'
    
    # Previous page link
    if current_page > 1:
        pagination_html += f'<li class="page-item"><a class="page-link pagination-link" data-page="{current_page - 1}" href="#">Previous</a></li>'
    
    # Page number links
    for page in range(1, total_pages + 1):
        active_class = 'active' if page == current_page else ''
        pagination_html += f'<li class="page-item {active_class}"><a class="page-link pagination-link" data-page="{page}" href="#">{page}</a></li>'
    
    # Next page link
    if current_page < total_pages:
        pagination_html += f'<li class="page-item"><a class="page-link pagination-link" data-page="{current_page + 1}" href="#">Next</a></li>'
    
    pagination_html += '</ul>'
    return pagination_html

# Function to check if the user is authenticated before each request
def require_login():
    # Add routes that do not require authentication to the following list
    allowed_routes = ['login', 'register', 'index', 'navbar']

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if the user is logged in
            if 'user_id' not in session and request.endpoint not in allowed_routes:
                flash('You need to login first.', 'error')
                return redirect(url_for('login_page'))

            # Check if the user is an admin, if the route requires admin privileges
            if 'admin' in request.endpoint and not is_admin(session.get('user_id')):
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)

        return wrapper

    return decorator


# Get user information to display in page.
def get_current_user_info():
    user_id = session.get('user_id')
    if user_id:
        with Session() as db_session:
            user = db_session.query(User).get(user_id)
            if user:
                return user
    return None


# Function to check if the logged-in user is an admin
def is_admin(user_id):
    with Session() as db_session:
        user = db_session.query(User).get(user_id)
        if user:
            return user.is_admin
        return False


# Function that sends an email whenever a new user is registered.
def send_notification_email(new_user_info):
    html = Template(Path('mail.html').read_text())
    with Session() as db_session:
        admin_emails = [user.email for user in db_session.query(
            User).filter_by(is_admin=True).all()]

    for admin_email in admin_emails:
        message = EmailMessage()
        message['from'] = 'Click & Buy - Mailer'
        message['to'] = admin_email
        message['subject'] = 'New User Registration Notification'
        message.set_content(html.substitute(
            name=new_user_info['name'], email=new_user_info['email']), 'html')

        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login('johandrehdb@gmail.com', 'afjtruqujroeylvx')
            smtp.send_message(message)


@app.route('/')
@app.route('/index')
def index():
    # Check if the user is authenticated
    if 'user_id' in session:
        # User is authenticated, redirect to the dashboard page
        return redirect(url_for('dashboard'))

    # User is not authenticated, you can redirect to the login page or a more generic home page
    # return redirect(url_for('login_page'))
    return render_template('index.html')


# ... (other filters and imports) ...

@app.route('/dashboard', methods=['GET', 'POST'])
@require_login()
def dashboard():
    min_price = request.form.get('min_price_filter')
    max_price = request.form.get('max_price_filter')

    if min_price and max_price and float(min_price) > float(max_price):
        flash("Minimum price cannot be higher than maximum price", "warning")



    def apply_numeric_filter(property_attr, filter_value):
        if filter_value == '1':
            return Property.bathrooms == 1
        elif filter_value == '2':
            return (property_attr == 2) & (property_attr.isnot(None))
        elif filter_value == '2+':
            return (property_attr >= 2) & (property_attr.isnot(None))
        elif filter_value == '3':
            return (property_attr == 3) & (property_attr.isnot(None))
        elif filter_value == '3+':
            return (property_attr >= 3) & (property_attr.isnot(None))
        return None

    def build_filters_from_form(form_data):
        filters = {
            'area_filter': form_data.get('area_filter'),
            'min_price_filter': form_data.get('min_price_filter'),
            'max_price_filter': form_data.get('max_price_filter'),
            'street_name_filter': form_data.get('street_name_filter'),
            'complex_name_filter': form_data.get('complex_name_filter'),
            'number_filter': form_data.get('number_filter'),
            'bedroom_filter': form_data.get('bedroom_filter'),
            'bathroom_filter': form_data.get('bathroom_filter'),
            'garages_filter': form_data.get('garages_filter'),
            'swimming_pool_filter': form_data.get('swimming_pool_filter'),
            'garden_flat_filter': form_data.get('garden_flat_filter'),
            'study_filter': form_data.get('study_filter'),
            'ground_floor_filter': form_data.get('ground_floor_filter'),
            'pet_friendly_filter': form_data.get('pet_friendly_filter'),
            # Add other filters here...
        }
        return filters

    def build_filters_from_request_args(args):
        filters = {
            'area_filter': args.get('area_filter'),
            'min_price_filter': args.get('min_price_filter'),
            'max_price_filter': args.get('max_price_filter'),
            'street_name_filter': args.get('street_name_filter'),
            'complex_name_filter': args.get('complex_name_filter'),
            'number_filter': args.get('number_filter'),
            'bedroom_filter': args.get('bedroom_filter'),
            'bathroom_filter': args.get('bathroom_filter'),
            'garages_filter': args.get('garages_filter'),
            'swimming_pool_filter': args.get('swimming_pool_filter'),
            'garden_flat_filter': args.get('garden_flat_filter'),
            'study_filter': args.get('study_filter'),
            'ground_floor_filter': args.get('ground_floor_filter'),
            'pet_friendly_filter': args.get('pet_friendly_filter'),
            # Add other filters here...
        }
        return filters

    def apply_filters(query, filters):
        filter_clauses = []

        if filters['area_filter']:
            areas = filters['area_filter'].split(',')  # Split areas into a list
            area_clauses = [Property.area.ilike(f"%{area.strip().lower()}%") for area in areas]
            filter_clauses.append(or_(*area_clauses))

        if filters['min_price_filter']:
            filter_clauses.append(
                Property.price >= filters['min_price_filter'])
        if filters['max_price_filter']:
            filter_clauses.append(
                Property.price <= filters['max_price_filter'])
        if filters['street_name_filter']:
            filter_clauses.append(func.lower(Property.street_name).ilike(f"%{filters['street_name_filter'].lower()}%"))

        if filters['complex_name_filter']:
            complex_name_clause = or_(
                func.lower(Property.complex_name).ilike(f"%{filters['complex_name_filter'].lower()}%"),
                func.lower(Property.street_name).ilike(f"%{filters['complex_name_filter'].lower()}%")
            )
            filter_clauses.append(complex_name_clause)

        if filters['number_filter']:
            number_clause = or_(
                Property.street_number == filters['number_filter'],
                Property.complex_number == filters['number_filter']
            )
            filter_clauses.append(number_clause)
        if filters['bedroom_filter']:
            bedroom_clause = apply_numeric_filter(
                Property.bedrooms, filters['bedroom_filter'])
            filter_clauses.append(bedroom_clause)
        if filters['bathroom_filter']:
            bathroom_clause = apply_numeric_filter(
                Property.bathrooms, filters['bathroom_filter'])
            filter_clauses.append(bathroom_clause)
        if filters['garages_filter']:
            garages_clause = apply_numeric_filter(
                Property.garages, filters['garages_filter'])
            filter_clauses.append(garages_clause)
        if filters['swimming_pool_filter']:
            filter_clauses.append(Property.swimming_pool == True)
        if filters['garden_flat_filter']:
            filter_clauses.append(Property.garden_flat == True)


        if filters['study_filter']:
            filter_clauses.append(Property.study == filters['study_filter'])
        if filters['ground_floor_filter']:
            filter_clauses.append(Property.ground_floor ==
                                  filters['ground_floor_filter'])
        if filters['pet_friendly_filter']:
            filter_clauses.append(Property.pet_friendly ==
                                  filters['pet_friendly_filter'])

        # Combine all filter clauses using AND
        if filter_clauses:
            query = query.filter(and_(*filter_clauses))

        return query

    def get_filtered_params(args):
        return {k: v for k, v in args.items() if k != 'page'}

    user = get_current_user_info()
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of properties per page

    if user:
        properties_query = Property.query

        # Handle filtering
        if request.method == 'POST':
            filters = build_filters_from_form(request.form)
            properties_query = apply_filters(properties_query, filters)
            print("Filters:", filters)
        else:
            filters = build_filters_from_request_args(request.args)
            properties_query = apply_filters(properties_query, filters)

        filtered_properties = properties_query.paginate(
            page=page, per_page=per_page)
        selected_areas = [area for area in properties_query.with_entities(
            Property.area).distinct()]
        
        total_pages = properties_query.paginate(
        page=page, per_page=per_page).total
        current_page = page
        pagination_html = generate_pagination_html(total_pages, current_page)
        paginationHTML = generate_pagination_html(
                        filtered_properties.pages, filtered_properties.page)
        
        if request.method == 'POST':
            properties_data = {
                'properties': [property.serialize() for property in filtered_properties.items],
                'pagination': {
                    'total': filtered_properties.total,
                    'per_page': filtered_properties.per_page,
                    'current_page': filtered_properties.page,
                    'pages': filtered_properties.pages,
                    'paginationHTML': generate_pagination_html(
                        filtered_properties.pages, filtered_properties.page)  # Update this line
                }
            }
            # print("Sending properties data:", properties_data)  # Debug log
            return jsonify(properties_data)  # Return JSON for AJAX requests
        
        return render_template('dashboard.html',
                               user=user,
                               properties=filtered_properties,
                               selected_areas=[],
                               filters=filters,
                               min_price_filter=filters.get('min_price_filter'),
                               max_price_filter=filters.get('max_price_filter'),
                               street_name_filter=filters.get('street_name_filter'),
                               complex_name_filter=filters.get('complex_name_filter'),
                               number_filter=filters.get('number_filter'),
                               bathroom_filter=filters.get('bathroom_filter'),
                               bedroom_filter=filters.get('bedroom_filter'),
                               garages_filter=filters.get('garages_filter'),
                               swimming_pool_filter=filters.get('swimming_pool_filter'),
                               garden_flat_filter=filters.get('garden_flat_filter'),
                               study_filter=filters.get('study_filter'),
                               ground_floor_filter=filters.get('ground_floor_filter'),
                               pet_friendly_filter=filters.get('pet_friendly_filter'),
                               get_filtered_params=get_filtered_params,
                               pagination_html=paginationHTML)
    else:
        flash('You need to login first.', 'error')
        return redirect(url_for('login_page'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    # Check if the user is already logged in
    if 'user_id' in session:
        # Redirect to dashboard if logged in
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')

        # Query the database to find the user with the provided email
        with Session() as db_session:
            user = db_session.query(User).filter_by(
                email=email).options(joinedload(User.login)).first()

            # Verify if the user exists and if the password (hash) is correct
            if user and check_password_hash(user.login[0].hash, password) and user.has_access:
                # User is authenticated, store user info in Flask's session
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                flash('You have successfully logged in.', 'success')
                # Redirect to the homepage or any other page after successful login
                return redirect(url_for('index'))
            else:
                # Invalid credentials, show an error message or redirect to the login page
                flash(
                    'Login failed. Please check your credentials or contact an administrator.', 'error')
                return redirect(url_for('login_page'))

    # For GET requests, render the login page
    return render_template('login.html')

# Route to fetch all users from the database


@app.route('/users', methods=['GET'])
@require_login()
def get_users():
    session = Session()
    users = session.query(User).all()
    session.close()
    return jsonify([user.name for user in users])


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    print("Received POST request to /register")
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate the form data (optional, add your validation logic here)

        # Check if the user already exists in the database
        session = Session()
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            session.close()
            return jsonify({'error': 'User with this email already exists'}), 400

        # Hash the password for security
        hashed_password = generate_password_hash(password)

        # Save the user data in the database
        new_user = User(name=first_name, surname=last_name,
                        email=email, joined=datetime.now())
        # Update 'email' to 'user_email'
        new_login = Login(hash=hashed_password, user_email=email)
        new_user.login.append(new_login)
        session.add(new_user)
        session.commit()
        session.close()

        # Generate new user info and runs the mailer to inform admins that a new user is registered.
        new_user_info = {
            'name': first_name,
            'email': email,
        }
        send_notification_email(new_user_info)

        # Return a success response
        return redirect(url_for('thank_you'))

    # Return an error response if the request method is not POST
    elif request.method == 'GET':
        # Replace 'register.html' with your registration form template
        return render_template('register.html')

    return jsonify({'error': 'Invalid request method'}), 400


@app.route('/logout')
def logout():
    # Clear the user's session data to log them out
    session.clear()

    # Create a response with cache control headers
    response = make_response(redirect(url_for('login_page')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    # You can also show a logout success message if you want
    flash('You have been logged out.', 'info')

    # Return the response with cache control headers
    return response


@app.context_processor
def pending_approval():
    with Session() as db_session:
        pending_users = db_session.query(
            User).filter_by(has_access=False).count()
        return dict(pending_users=pending_users)


@app.route('/get_pending_users_count')
def get_pending_users_count():
    with Session() as db_session:
        pending_users = db_session.query(
            User).filter_by(has_access=False).count()
        return jsonify(pending_users=pending_users)


@app.route('/admin_users')
def admin_users():
    # Check if the user is an admin
    if 'user_id' in session and session['is_admin']:
        # Retrieve the list of all users from the database
        with Session() as db_session:
            users = db_session.query(User).all()

        # Retrieve the current user's information
        current_user = get_current_user_info()

        # Render the admin_users template and pass the list of users
        return render_template('admin_users.html', users=users, user=current_user)
    else:
        flash('You need to be logged in as an admin to access this page.', 'error')
        return redirect(url_for('login_page'))


@app.route('/admin/users/<int:user_id>/delete', methods=['GET', 'POST'])
def admin_delete_user(user_id):
    # Check if the user is logged in and is an admin
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))

    # Get the user from the database
    with Session() as db_session:
        user = db_session.query(User).get(user_id)

        # Check if the user exists
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        if user:
            login = db_session.query(Login).filter_by(
                user_email=user.email).first()
            if login:
                db_session.delete(user)
                db_session.delete(login)
                db_session.commit()
        # Delete the user

    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash('You need to be logged in as an admin to edit users.', 'error')
        return redirect(url_for('dashboard'))

    # Check if the request method is POST, indicating a form submission
    if request.method == 'POST':
        # Get the new admin status from the form
        is_admin_new = request.form.get('is_admin')
        has_access = request.form.get('has_access')

        # Load the user from the database
        with Session() as db_session:
            user = db_session.query(User).get(user_id)
            new_name = request.form.get('name')
            new_email = request.form.get('email')
            new_surname = request.form.get('surname')

            # Check if the user exists
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('admin_users'))

            # Update the user's admin status
            user.name = new_name
            user.email = new_email
            user.surname = new_surname
            user.is_admin = bool(is_admin_new)
            user.has_access = bool(has_access)
            db_session.commit()

            # Print the user's details for debugging purposes
            print("User ID:", user.id)
            print("User Name:", user.name)
            print("Is Admin:", user.is_admin)

            flash('User updated successfully.', 'success')
            return redirect(url_for('admin_users'))

    # If the request method is GET, render the admin_edit_user.html template
    else:
        # Load the user from the database
        with Session() as db_session:
            user = db_session.query(User).get(user_id)

            # Check if the user exists
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('admin_users'))

            return render_template('admin_edit_user.html', user=user)


@app.route('/thank_you', methods=['GET'])
def thank_you():
    return render_template('thank_you.html')


@app.route('/<string:page_name>')
def html_page(page_name):
    user = get_current_user_info()
    return render_template(page_name + '.html', user=user)


@app.route('/pages/<path:page_name>')
def load_html_page(page_name):
    user = get_current_user_info()
    return render_template('pages/' + page_name + '.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
