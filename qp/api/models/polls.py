from datetime import datetime

import sqlalchemy
from sqlalchemy import orm

from .users import User
from ..database.db_session import SqlAlchemyBase


class Poll(SqlAlchemyBase):
    __tablename__ = "polls"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(User.id), nullable=False)
    completed = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    private = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    deleted = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)

    author = orm.relation(User)
    options = orm.relation("Option", back_populates="poll", passive_deletes=True)
    comments = orm.relation("Comment", back_populates="poll", order_by="desc(Comment.created_at)", passive_deletes=True)

    max_title_length = 100
    max_description_length = 2000
    min_options_count = 1
    max_options_count = 15

    def __repr__(self):
        return f"<Poll> {self.id} {self.title}"


class Option(SqlAlchemyBase):
    __tablename__ = "options"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    poll_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(Poll.id, ondelete="CASCADE"), nullable=False)

    poll = orm.relation(Poll)
    users = orm.relation(User, secondary="votes", passive_deletes=True)

    max_title_length = 100

    def __repr__(self):
        return f"<Option> {self.id} {self.title} ({self.poll.title})"


class Vote(SqlAlchemyBase):
    __tablename__ = "votes"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    option_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(Option.id, ondelete="CASCADE"),
                                  nullable=False)

    user = orm.relation(User)
    option = orm.relation(Option)

    def __repr__(self):
        return f"<Vote> {self.id} {self.user.username} {self.option.title} ({self.option.poll.title})"


class Comment(SqlAlchemyBase):
    __tablename__ = "comments"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(User.id), nullable=False)
    poll_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(Poll.id, ondelete="CASCADE"), nullable=False)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)

    user = orm.relation(User)
    poll = orm.relation(Poll)

    max_text_length = 400

    def __repr__(self):
        return f"<Comment> {self.id} {self.user.username})"
