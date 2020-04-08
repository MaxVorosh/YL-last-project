from sqlalchemy import Column, Integer, String, ForeignKey, Text, Datetime
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Deal(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product = Column(Integer, ForeignKey("products.id"))
    participants = Column(String)
    history = Column(Text, nullable=True)
    date = Column(Datetime)
