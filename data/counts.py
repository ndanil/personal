import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Counts(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'counts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    userid = sqlalchemy.Column(sqlalchemy.Integer)
    catid = sqlalchemy.Column(sqlalchemy.Integer)
    count = sqlalchemy.Column(sqlalchemy.Integer)
    updated = sqlalchemy.Column(sqlalchemy.DateTime)
