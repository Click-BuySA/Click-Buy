from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, make_response
from sqlalchemy import create_engine, or_, and_, func
from sqlalchemy.orm import sessionmaker, joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import User, Login, Property, Base, db
from functools import wraps
import smtplib
from email.message import EmailMessage
from string import Template
from pathlib import Path
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 3600  # Set database time-out to 1 hour
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Automatically reconnect on connection loss
}

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

db.init_app(app)


smtp_email = os.getenv("SMTP_EMAIL")
smtp_password = os.getenv("SMTP_PASSWORD")

# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       Function Declarations
# <---------------------------------------------------------------------------------------------------------------------------------------->


@app.template_filter('format_currency')
def format_currency(value):
    if not isinstance(value, (int, float)):
        return ''  # Return an empty string for non-numeric values
    return f'R {value:,.2f}'

# Common Email Sending Function


def send_email(subject, recipients, content, cc=None):
    html_template = Template(content)
    html_content = html_template.substitute()

    message = EmailMessage()
    message['from'] = 'Click & Buy - Mailer'
    message['subject'] = subject
    message.set_content(html_content, 'html')

    with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(smtp_email, smtp_password)

        for recipient in recipients:
            message['to'] = recipient
            if cc:
                message['cc'] = cc  # Set the cc field if provided
            smtp.send_message(message)


def generate_pagination_html(total_pages, current_page):
    pagination_html = '<ul class="pagination pagination-links justify-content-center">'

    # Previous page link
    if current_page > 1:
        pagination_html += f'<li class="page-item"><a class="page-link pagination-link" data-page="{current_page - 1}" href="#"><</a></li>'

    # Page number links
    page_range = 1  # Number of pages to display on each side of the current page
    start_page = max(1, current_page - page_range)
    end_page = min(total_pages, current_page + page_range)

    if start_page > 1:
        pagination_html += '<li class="page-item disabled"><span class="page-link">...</span></li>'
    for page in range(start_page, end_page + 1):
        active_class = 'active' if page == current_page else ''
        pagination_html += f'<li class="page-item {active_class}"><a class="page-link pagination-link" data-page="{page}" href="#">{page}</a></li>'
    if end_page < total_pages:
        pagination_html += '<li class="page-item disabled"><span class="page-link">...</span></li>'

    # Next page link
    if current_page < total_pages:
        pagination_html += f'<li class="page-item"><a class="page-link pagination-link" data-page="{current_page + 1}" href="#">></a></li>'

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


# Function that sends a notification email whenever a new user is registered.
def send_notification_email(new_user_info, cc=None):
    # Load the email template from the templates folder
    template_path = os.path.join(os.path.dirname(
        __file__), 'templates', 'mail.html')
    html_template = Template(open(template_path, 'r').read())

    html_content = html_template.substitute(
        name=new_user_info['name'],
        surname=new_user_info['surname'],
        email=new_user_info['email']
    )

    with Session() as db_session:
        admin_emails = [user.email for user in db_session.query(
            User).filter_by(is_admin=True).all()]

    send_email(
        subject='New User Registration Notification',
        recipients=[admin_emails],
        content=html_content,
        cc=cc
    )


# Function to generate a password reset token
def generate_reset_token(length=32):
    return secrets.token_hex(length)


# Function to send reset mail to user
def send_password_reset_email(user, reset_token):
    subject = 'Password Reset for Your Click & Buy Account'
    recipients = [user.email]

    # Generate the reset link with the token
    reset_link = f'{reset_token}'

    # Create the email content using an HTML template
    content = f'''
    <p>Hello {user.name},</p>
    <p>You have requested to reset your password for your Click & Buy account.</p>
    <p>Please click the following link to reset your password:</p>
    <p><a href="{reset_link}">Reset Password</a></p>
    <p>If you did not request this password reset, please ignore this email.</p>
    <p>Best regards,<br>Your Click & Buy Team</p>
    '''

    # Send the email
    send_email(subject, recipients, content)


# Function for expiring tokens.
def is_token_expired(token_creation_time, expiration_duration):
    now = datetime.utcnow()
    token_age = now - token_creation_time
    return token_age > expiration_duration


# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       Routes Start
# <---------------------------------------------------------------------------------------------------------------------------------------->
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
    def apply_numeric_filter(property_attr, filter_value):
        if filter_value == '1':
            return property_attr == 1
        elif filter_value == '2':
            return (property_attr == 2) & (property_attr.isnot(None))
        elif filter_value == '2+':
            return (property_attr >= 2) & (property_attr.isnot(None))
        elif filter_value == '3':
            return (property_attr == 3) & (property_attr.isnot(None))
        elif filter_value == '3+':
            return (property_attr >= 3) & (property_attr.isnot(None))
        elif filter_value == '4+':
            return (property_attr >= 4) & (property_attr.isnot(None))
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
            'prop_type_filter': form_data.get('prop_type_filter'),
            'prop_category_filter': form_data.get('prop_category_filter'),
            'carports_filter': form_data.get('carports_filter'),
            'agent_filter': form_data.get('agent_filter'),
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
            'prop_type_filter': args.get('prop_type_filter'),
            'prop_category_filter': args.get('prop_category_filter'),
            'carports_filter': args.get('carports_filter'),
            'agent_filter': args.get('agent_filter'),
            # Add other filters here...
        }
        return filters

    def apply_filters(query, filters):
        filter_clauses = []

        if filters['area_filter']:
            areas = filters['area_filter'].split(
                ',')  # Split areas into a list
            area_clauses = [Property.area.ilike(
                f"%{area.strip().lower()}%") for area in areas]
            filter_clauses.append(or_(*area_clauses))

        if filters['min_price_filter']:
            filter_clauses.append(
                Property.price >= filters['min_price_filter'])
        if filters['max_price_filter']:
            filter_clauses.append(
                Property.price <= filters['max_price_filter'])

        if filters['street_name_filter']:
            filter_clauses.append(func.lower(Property.street_name).ilike(
                f"%{filters['street_name_filter'].lower()}%"))
            
        if filters['agent_filter']:
            filter_clauses.append(func.lower(Property.agent).ilike(
                f"%{filters['agent_filter'].lower()}%"))

        if filters['complex_name_filter']:
            complex_name_clause = or_(
                func.lower(Property.complex_name).ilike(
                    f"%{filters['complex_name_filter'].lower()}%"),
                func.lower(Property.street_name).ilike(
                    f"%{filters['complex_name_filter'].lower()}%")
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
        if filters['carports_filter']:
            carports_clause = apply_numeric_filter(
                Property.carports, filters['carports_filter'])
            filter_clauses.append(carports_clause)
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
        if filters['prop_type_filter'] == 'Any':
            # Do nothing for 'Any'
            pass
        else:
            filter_clauses.append(Property.prop_type ==
                                  filters['prop_type_filter'])

        if filters['prop_category_filter'] == 'Any':
            # Do nothing for 'Any'
            pass
        else:
            filter_clauses.append(Property.prop_category ==
                                  filters['prop_category_filter'])

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
            return jsonify(properties_data)  # Return JSON for AJAX requests

        return render_template('dashboard.html',
                               user=user,
                               properties=filtered_properties,
                               selected_areas=[],
                               filters=filters,
                               min_price_filter=filters.get(
                                   'min_price_filter'),
                               max_price_filter=filters.get(
                                   'max_price_filter'),
                               street_name_filter=filters.get(
                                   'street_name_filter'),
                               complex_name_filter=filters.get(
                                   'complex_name_filter'),
                               number_filter=filters.get('number_filter'),
                               bathroom_filter=filters.get('bathroom_filter'),
                               bedroom_filter=filters.get('bedroom_filter'),
                               garages_filter=filters.get('garages_filter'),
                               swimming_pool_filter=filters.get(
                                   'swimming_pool_filter'),
                               garden_flat_filter=filters.get(
                                   'garden_flat_filter'),
                               study_filter=filters.get('study_filter'),
                               ground_floor_filter=filters.get(
                                   'ground_floor_filter'),
                               pet_friendly_filter=filters.get(
                                   'pet_friendly_filter'),
                               prop_type_filter=filters.get(
                                   'prop_type_filter'),
                               prop_category_filter=filters.get(
                                   'prop_category_filter'),
                                carports_filter=filters.get('carports_filter'),
                                agent_filter=filters.get('agent_filter'),
                               get_filtered_params=get_filtered_params,
                               pagination_html=paginationHTML)
    else:
        flash('You need to login first.', 'error')
        return redirect(url_for('login_page'))


# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       Property Routes
# <---------------------------------------------------------------------------------------------------------------------------------------->

@app.route('/view_property/<int:property_id>')
@require_login()
def view_property(property_id):
    with Session() as db_session:
        user = get_current_user_info()
        property = db_session.query(Property).get(property_id)

        if not property:
            flash('Property not found.', 'error')
            return redirect(url_for('dashboard'))

        return render_template('property_details.html', user=user, property=property)


@app.route('/update_property/<int:property_id>', methods=['POST'])
@require_login()
def update_property(property_id):
    if session['is_admin']:
        with Session() as db_session:
            property = db_session.query(Property).get(property_id)

            if not property:
                flash('Property not found.', 'error')
                return redirect(url_for('dashboard'))

            # Update property attributes based on form data
            property.street_number = request.form.get('street_number') or None
            property.street_name = request.form.get('street_name') or None
            complex_name = request.form.get('complex_name')
            property.complex_name = complex_name if complex_name != 'None' and complex_name else None
            property.complex_name = request.form.get('complex_name') or None
            property.area = request.form.get('area')
            property.price = request.form.get('price')
            bedrooms = request.form.get('bedrooms')
            property.bedrooms = int(
                bedrooms) if bedrooms else None if bedrooms != '' else None
            bathrooms = request.form.get('bathrooms')
            property.bathrooms = float(
                bathrooms) if bathrooms else None if bathrooms != '' else None
            garages = request.form.get('garages')
            property.garages = int(
                garages) if garages else None if garages != '' else None
            property.link = request.form.get('link')
            property.link_display = request.form.get('link_display')
            property.swimming_pool = bool(request.form.get('swimming_pool'))
            property.garden_flat = bool(request.form.get('garden_flat'))
            property.study = bool(request.form.get('study'))
            property.ground_floor = bool(request.form.get('ground_floor'))
            property.prop_type = request.form.get('prop_type')
            property.prop_category = request.form.get('prop_category')
            property.carports = request.form.get('carports')
            property.agent = request.form.get('agent')
            # Only commit changes if there are non-empty fields
            if any([
                property.price,
                property.bathrooms is not None,
                property.garages is not None,
                property.bedrooms is not None,
                # Add other conditions for numeric fields
            ]):

                # Update other attributes similarly

                db_session.commit()
                flash('Property information updated successfully.', 'success')
    else:
        flash('You do not have permission to edit this property.', 'error')

    return redirect(url_for('view_property', property_id=property_id))


@app.route('/delete_property/<int:property_id>', methods=['POST'])
@require_login()
def delete_property(property_id):
    if session['is_admin']:
        with Session() as db_session:
            property_to_delete = db_session.query(Property).get(property_id)

            if not property_to_delete:
                flash('Property not found.', 'error')
                return redirect(url_for('dashboard'))

            db_session.delete(property_to_delete)
            db_session.commit()

            flash('Property deleted successfully.', 'success')
    else:
        flash('You do not have permission to delete this property.', 'error')

    return redirect(url_for('dashboard'))


@app.route('/add_property', methods=['GET', 'POST'])
@require_login()
def add_property():
    user_id = session.get('user_id')
    if user_id:
        with Session() as db_session:
            user = db_session.query(User).get(user_id)

    # Check if the user is an admin
    if 'user_id' in session and session['is_admin']:
        if request.method == 'POST':
            # Retrieve form data
            street_number = request.form.get('street_number')
            street_name = request.form.get('street_name')
            complex_number = request.form.get('complex_number')
            complex_name = request.form.get('complex_name')
            area = request.form.get('area')
            price = request.form.get('price')
            bedrooms = request.form.get('bedrooms')
            bathrooms = request.form.get('bathrooms')
            garages = request.form.get('garages')
            link = request.form.get('link')
            link_display = request.form.get('link_display')
            prop_category = request.form.get('prop_category')
            prop_type = request.form.get('prop_type')
            swimming_pool = 'swimming_pool' in request.form
            garden_flat = 'garden_flat' in request.form
            study = 'study' in request.form
            ground_floor = 'ground_floor' in request.form
            carports = request.form.get('carports')
            agent = request.form.get('agent')

            # Check if the input is an empty string, and if so, set it to None
            garages = int(garages) if garages.strip() else None
            bedrooms = int(bedrooms) if bedrooms.strip() else None
            bathrooms = int(bathrooms) if bathrooms.strip() else None

            # Create a Property object and add it to the database
            new_property = Property(
                street_number=street_number,
                street_name=street_name,
                complex_number=complex_number,
                complex_name=complex_name,
                area=area,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                garages=garages,
                link=link,
                link_display=link_display,
                swimming_pool=swimming_pool,
                garden_flat=garden_flat,
                study=study,
                ground_floor=ground_floor,
                carports=carports,
                agent=agent,
                prop_type=prop_type,
                prop_category=prop_category
            )
            db.session.add(new_property)
            db.session.commit()

            flash('Property added successfully!', 'success')
            return redirect(url_for('dashboard'))

        # For GET requests, render the add_property.html template
        return render_template('add_property.html', user=user)

    else:
        flash('You need to be logged in as an admin to access this page.', 'error')
        return redirect(url_for('login_page'))

# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       Authentication Routes
# <---------------------------------------------------------------------------------------------------------------------------------------->


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
                # Store the user's email in the session
                session['user_email'] = user.email
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
            'surname': last_name,
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

# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                      Administrator Routes
# <---------------------------------------------------------------------------------------------------------------------------------------->


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


@app.route('/send_email', methods=['POST'])
def send_email_route():
    try:

        with Session() as db_session:
            admin_emails = [user.email for user in db_session.query(
                User).filter_by(is_admin=True).all()]

        # Get selected property IDs from the request
        selected_properties = request.get_json()

        # Get the user's email from the session
        # Adjust the session key as needed
        user_email = session.get('user_email')

        if user_email is None:
            flash("User email not found in session.", "danger")
            return jsonify({"message": "error"})

        # Generate the list of property details
        properties_list = ""
        for property in selected_properties:
            property_id = property.get('id', 'N/A')
            description = property.get('description', 'N/A')
            price = property.get('price', 'N/A')
            beds = property.get('beds', 'N/A')
            baths = property.get('baths', 'N/A')
            garages = property.get('garages', 'N/A')
            link_display = property.get('link_display', 'N/A')
            link = property.get('link', 'N/A')

            property_item = """
            <div class="column">
                <div class="card">
                    <h3>{description}</h3>
                    <p><strong>Price:</strong> {price}</p>
                    <p><strong>Beds:</strong> {beds}</p>
                    <p><strong>Baths:</strong> {baths}</p>
                    <p><strong>Garages:</strong> {garages}</p>
                    <p><strong>Link:</strong> <a href="{link}">{link_display}</a></p>
                </div>
            </div>
            """.format(
                id=property_id,
                description=description,
                price=price,
                beds=beds,
                baths=baths,
                garages=garages,
                link_display=link_display,
                link=link
            )
            properties_list += property_item

        # Load the export template and format the content
        template_path = os.path.join(os.path.dirname(
            __file__), 'templates', 'export_template.html')
        with open(template_path, 'r') as template_file:
            email_content = template_file.read().replace(
                '{properties}', properties_list)

        # Send the email
        send_email(
            subject="Property Export",
            recipients=[user_email],
            content=email_content,
            cc=admin_emails
        )

        flash("Export successful to " + user_email, "success")
        return jsonify({"message": "success", "email": user_email})
    except Exception as e:
        print("Exception:", e)  # Print the exception details
        flash("Export failed. Please contact an administrator.", "danger")
        return jsonify({"message": "error"})


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


# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       Mailer Routes
# <---------------------------------------------------------------------------------------------------------------------------------------->

@app.route('/thank_you', methods=['GET'])
def thank_you():
    return render_template('thank_you.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    user = get_current_user_info()
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')

            email_content = f'''
            <html>
            <head></head>
            <body>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong> {message}</p>
            </body>
            </html>
            '''
            # Send the email
            send_email(
                subject="Contact Form Submission",
                # Replace with your admin email
                recipients=[smtp_email],
                content=email_content
            )

            flash("Message sent successfully.", "success")
        except Exception as e:
            print("Exception:", e)
            flash("Message failed to send. Please try again later.", "danger")

        # Redirect back to the contact page
        return redirect(url_for('contact'))

    # For GET requests, render the contact form template
    return render_template('contact.html', user=user)


@app.route('/report', methods=['GET', 'POST'])
@require_login()
def report_issue():
    user = get_current_user_info()
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        name = request.form.get('name')
        email = request.form.get('email')

        with Session() as db_session:
            admin_emails = [user.email for user in db_session.query(
                User).filter_by(is_admin=True).all()]

        # Prepare email content
        email_subject = f'Issue Report: {subject}'

        # Render the email template with the provided data
        email_content = render_template('mail_report.html',
                                        name=name,
                                        email=email,
                                        subject=subject,
                                        message=message)

        # Send email to admins using your send_email function
        send_email(email_subject, [admin_emails], email_content)

        flash('Issue reported successfully. Thank you!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('report.html', user=user)


@app.route('/change_password', methods=['GET', 'POST'])
@require_login()
def change_password():
    user = get_current_user_info()

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        with Session() as db_session:
            user = db_session.query(User).filter_by(
                email=user.email).options(joinedload(User.login)).first()

            if not check_password_hash(user.login[0].hash, current_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
            else:
                new_password_hash = generate_password_hash(new_password)
                db_session.query(Login).filter_by(user_email=user.email).update(
                    {'hash': new_password_hash})  # Update the filter
                db_session.commit()
                flash('Password changed successfully.', 'success')
                return redirect(url_for('dashboard'))

            return redirect(url_for('change_password'))

    return render_template('change_password.html', user=user)

# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       User Routes
# <---------------------------------------------------------------------------------------------------------------------------------------->


@app.route('/account_settings', methods=['GET', 'POST'])
@require_login()
def account_settings():
    user_id = session.get('user_id')
    if user_id:
        with Session() as db_session:
            user = db_session.query(User).get(user_id)

            if request.method == 'POST':
                new_name = request.form.get('name')
                new_surname = request.form.get('surname')
                new_email = request.form.get('email')

                # Update user information
                user.name = new_name
                user.surname = new_surname
                user.email = new_email

                # Commit changes
                db_session.commit()

                flash('User information updated successfully.', 'success')
                return redirect(url_for('account_settings'))

            return render_template('account_settings.html', user=user)

    flash('You need to be logged in to access this page.', 'error')
    return redirect(url_for('login_page'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        with Session() as db_session:
            user = db_session.query(User).filter_by(email=email).first()

            if user:
                # Generate a unique reset token and store it in the database
                reset_token = generate_reset_token()
                user.reset_token = reset_token
                user.reset_token_created_at = datetime.utcnow()
                db_session.commit()

                # Send reset link via email
                reset_link = url_for(
                    'reset_password', token=reset_token, _external=True)
                send_password_reset_email(user, reset_link)

                flash('A password reset link has been sent to your email.', 'info')
                return redirect(url_for('login_page'))
            else:
                flash('No user with that email address found.', 'error')

    return render_template('forgot_password.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    with Session() as db_session:

        token = request.args.get('token')
        user = db_session.query(User).filter_by(reset_token=token).first()
        # Check if the token is expired
        if is_token_expired(user.reset_token_created_at, timedelta(hours=1)):
            return "Token has expired. Please request a new password reset."

        if not user:
            flash(
                'Invalid or expired reset token. Please request a new password reset.', 'error')
            return redirect(url_for('login_page'))

        if request.method == 'POST':
            # Update the user's password and remove the reset token
            new_password = request.form.get('new_password')
            user.login[0].hash = generate_password_hash(new_password)
            user.reset_token = None  # Remove the reset token
            user.reset_token_created_at = None
            db_session.commit()
            flash(
                'Password reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('login_page'))

        return render_template('reset_password.html', token=token)

# <---------------------------------------------------------------------------------------------------------------------------------------->
#                                                                       Generic Routes
# <---------------------------------------------------------------------------------------------------------------------------------------->
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
