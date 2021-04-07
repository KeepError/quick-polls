from datetime import datetime

import sqlalchemy
from sqlalchemy import orm

from data.db_session import SqlAlchemyBase


class Poll(SqlAlchemyBase):
    __tablename__ = "polls"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    author = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    completed = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)

    author_obj = orm.relation("User")

    def __repr__(self):
        return f"<Poll> {self.id} {self.title}"


class Option(SqlAlchemyBase):
    __tablename__ = "options"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    poll = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(Poll.id))

    poll_obj = orm.relation(Poll)

    def __repr__(self):
        return f"<Option> {self.id} {self.title}"