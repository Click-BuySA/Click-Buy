from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Login

DATABASE_URI = 'postgresql://postgres:SQLPassX&7@localhost/click_and_buy'
engine = create_engine(DATABASE_URI)
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()

def clear_data():
    # Delete all data from the 'login' table
    session.query(Login).delete()
    # Delete all data from the 'users' table
    session.query(User).delete()
    # Commit the changes to the database
    session.commit()

if __name__ == '__main__':
    clear_data()
    print("All data from 'users' and 'login' tables has been cleared.")
