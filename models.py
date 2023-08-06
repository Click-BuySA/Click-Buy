# models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    surname = Column(String(100))
    email = Column(String(100), unique=True)
    joined = Column(DateTime)
    is_admin = Column(Boolean, default=False)

    login = relationship("Login", back_populates='user')


class Login(Base):
    __tablename__ = 'login'
    id = Column(Integer, primary_key=True)
    hash = Column(String(255))  # Use Text data type for hash
    user_email = Column(String(255), ForeignKey('users.email'))
    user = relationship('User', back_populates='login')  # Add this line
