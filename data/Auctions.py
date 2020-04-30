from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Auction(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "auctions"
    id = Column(Integer, primary_key=True)
    product = Column(Integer, ForeignKey("products.id"))
    participants = Column(String)
    history = Column(Text, nullable=True)
    winner = Column(Integer, ForeignKey("users.id"), nullable=True)
    deal = Column(Integer, ForeignKey("deals.id"), nullable=True)
