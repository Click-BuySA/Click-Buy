from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Login
from werkzeug.security import generate_password_hash
from datetime import datetime


DATABASE_URI = 'postgresql://postgres:SQLPassX&7@localhost/click_and_buy'
engine = create_engine(DATABASE_URI)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def create_new_user():
    name='John',
    surname='Doe',
    email='john@gmail.com',
    is_admin=False,  # Set the is_admin field to True for the admin user
    joined = datetime.now()

    # Check if the user already exists
    with DBSession() as session:
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            print("User already exists.")
            return

    print("Creating admin user...")

    # Set the password for the admin user
    hashed_password = generate_password_hash('cookies')

    user = User(name=name, surname=surname, email=email, joined=joined, is_admin=is_admin)

    # Add the user to the session and commit changes to the users table
    session.add(user)
    session.commit()
    
#    Now, add the user to the login table as well
    login_user = session.query(User).filter_by(email=email).first()
    if login_user:
        # Update the password hash in the login table
        login_user.set_password_hash(hashed_password)
        session.commit()
    else:
        # If the user doesn't exist in the login table, create a new entry
        login_user = Login(user_email=email, hash=hashed_password)
        session.add(login_user)
        session.commit()
    print("User created successfully.")


if __name__ == "__main__":
    create_new_user()
