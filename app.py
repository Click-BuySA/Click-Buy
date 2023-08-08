from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, make_response
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import sessionmaker, joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import Base, User, Login
from functools import wraps

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'

# Replace 'your_database_name' with your actual database name
DATABASE_URI = 'postgresql://postgres:SQLPassX&7@localhost/click_and_buy'
engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


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

# @app.route('/dashboard.html')
@app.route('/dashboard')
@require_login()
def dashboard():
    # Render the dashboard template
    user = get_current_user_info()
    if user:
        return render_template('dashboard.html', user=user)
    else:
        flash('You need to login first.', 'error')
        return redirect(url_for('login_page'))



@app.route('/login', methods=['GET', 'POST'])
# @app.route('/login.html', methods=['GET', 'POST'])
def login_page():
    # Check if the user is already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))  # Redirect to dashboard if logged in
    
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')

        # Query the database to find the user with the provided email
        with Session() as db_session:
            user = db_session.query(User).filter_by(
                email=email).options(joinedload(User.login)).first()

            # Verify if the user exists and if the password (hash) is correct
            if user and check_password_hash(user.login[0].hash, password):
                # User is authenticated, store user info in Flask's session
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                flash('You have successfully logged in.', 'success')
                # Redirect to the homepage or any other page after successful login
                return redirect(url_for('index'))
            else:
                # Invalid credentials, show an error message or redirect to the login page
                flash('Invalid email or password.', 'error')
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
# @app.route('/register.html', methods=['GET', 'POST'])
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

        # Return a success response
        return redirect(url_for('thank_you'))

    # Return an error response if the request method is not POST
    elif request.method == 'GET':
        # Replace 'register.html' with your registration form template
        return render_template('register.html')

    return jsonify({'error': 'Invalid request method'}), 400

@app.route('/logout')
# @app.route('/logout.html')
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


@app.route('/admin_users')
def admin_users():
    # Check if the user is an admin
    if 'user_id' in session and session['is_admin']:
        # Retrieve the list of all users from the database
        with Session() as db_session:
            users = db_session.query(User).all()

        # Render the admin_users template and pass the list of users
        return render_template('admin_users.html', users=users)
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
            login = db_session.query(Login).filter_by(user_email=user.email).first()
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
