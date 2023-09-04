# models.py

from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy 

db = SQLAlchemy()  # Initialize SQLAlchemy


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    surname = Column(String(100))
    email = Column(String(100), unique=True)
    joined = Column(DateTime)
    has_access = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    reset_token = Column(String(255), unique=True)
    reset_token_created_at = Column(DateTime)

    login = relationship("Login", back_populates='user')


class Login(Base):
    __tablename__ = 'login'
    id = Column(Integer, primary_key=True)
    hash = Column(String(255))  # Use Text data type for hash
    user_email = Column(String(255), ForeignKey('users.email'))
    user = relationship('User', back_populates='login')  # Add this line


class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    street_name = db.Column(db.String(100))
    street_number = db.Column(db.String(30))
    complex_name = db.Column(db.String(100))
    complex_number = db.Column(db.String(30))
    area = db.Column(db.String(30))
    price = db.Column(db.BigInteger)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Numeric(precision=2, scale=1))
    garages = db.Column(db.Integer)
    swimming_pool = db.Column(db.Boolean, default=False)
    garden_flat = db.Column(db.Boolean, default=False) 
    study = db.Column(db.Boolean, default=False)
    ground_floor = db.Column(db.Boolean, default=False)
    pet_friendly = db.Column(db.Boolean)
    link = db.Column(db.String(100))
    link_display = db.Column(db.String(30))
    note = db.Column(db.String(255))

    def serialize(self):
        return {
            'id': self.id,
            'street_number': self.street_number,
            'street_name': self.street_name,
            'complex_number': self.complex_number,
            'complex_name': self.complex_name,
            'area': self.area,
            'price': self.price,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'garages': self.garages,
            'swimming_pool': self.swimming_pool,
            'garden_flat': self.garden_flat,
            'study': self.study,
            'ground_floor': self.ground_floor,
            'pet_friendly': self.pet_friendly,
            'link': self.link,
            'link_display': self.link_display
            # ... Add other attributes here ...
        }

    def __repr__(self):
        return f"Property(id={self.id}, street_name={self.street_name}, price={self.price})"