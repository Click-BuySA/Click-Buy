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

def create_admin_user():
    # Check if there are any users in the database
    existing_users = session.query(User).all()

    # If there are no users in the database, create the first user as an admin
    if not existing_users:
        print("Creating admin user...")
        admin_user = User(
            name='Johandré',
            surname='de Beer',
            email='johandrehdb@gmail.com',
            is_admin=True,  # Set the is_admin field to True for the admin user
            joined = datetime.now()
        )
        session.add(admin_user)

        # Set the password for the admin user
        hashed_password = generate_password_hash('passwordX&7')
        
        # Create the login entry for the admin user
        admin_login = Login(hash=hashed_password, user=admin_user)
        session.add(admin_login)
        session.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    create_admin_user()
