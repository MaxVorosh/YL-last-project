from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
import datetime


class User(UserMixin, SqlAlchemyBase, SerializerMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    surname = Column(String)
    products = Column(String, nullable=True)
    deals = Column(String, nullable=True)
    auctions = Column(String, nullable=True)
    registration_date = Column(DateTime, default=datetime.datetime.now)
    role = Column(String, default="user")
    email = Column(String, unique=True)
    password = Column(String)
    money = Column(Float, default=0.00)
