from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field

from ..models.users import User


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        exclude = ("hashed_password",)
        load_only = ("password",)

    password = auto_field("hashed_password")