from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Product(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    owner = Column(Integer, ForeignKey("users.id"))
