import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Categories(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'categories'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    userid = sqlalchemy.Column(sqlalchemy.Integer)
    title = sqlalchemy.Column(sqlalchemy.String)
