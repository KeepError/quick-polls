from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_restful import Api, Resource
from marshmallow.exceptions import ValidationError

from ..database import db_session
from ..tools import errors
from ..models.users import User, generate_password
from ..tools.response import make_success_message
from ..tools.decorators import admin_required
from ..schemas.users import UserSchema

blueprint = Blueprint(
    "users_resource",
    __name__,
)
api = Api(blueprint)


def get_user_tokens(user_data):
    access_token = create_access_token(identity=user_data)
    refresh_token = create_refresh_token(identity=user_data)
    return {"access_token": access_token,
            "refresh_token": refresh_token}


class UserResource(Resource):
    @admin_required()
    def get(self, username):
        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError
        data = UserSchema().dump(user)
        return jsonify({"user": data})

    @admin_required()
    def put(self, username):
        data = request.get_json()
        try:
            UserSchema(partial=True).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        if "password" in data:
            data["hashed_password"] = generate_password(data.pop("password"))
        session.query(User).filter(User.username == username).update(data)
        session.commit()
        return make_success_message()

    @admin_required()
    def delete(self, username):
        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        session.delete(user)
        session.commit()
        return make_success_message()


class UsersListResource(Resource):
    @admin_required()
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({
            "users": UserSchema().dump(users, many=True)
        })

    @admin_required()
    def post(self):
        data = request.get_json()
        try:
            UserSchema().load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()

        result = session.query(User).filter((User.username == data["username"]) | (User.email == data["email"])).first()
        if result is not None:
            raise errors.UserAlreadyExistsError

        password = data.pop("password")
        user = User(**data)
        user.set_password(password)
        session.add(user)
        session.commit()

        return make_success_message({"user": UserSchema().dump(user)})


class UserRegisterResource(Resource):
    def post(self):
        data = request.get_json()
        try:
            UserSchema(only=("email", "username", "password")).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()

        result = session.query(User).filter((User.username == data["username"]) | (User.email == data["email"])).first()
        if result is not None:
            raise errors.UserAlreadyExistsError

        password = data.pop("password")
        user = User(**data)
        user.set_password(password)
        session.add(user)
        session.commit()

        return jsonify(get_user_tokens(user.id))


class UserLoginResource(Resource):
    def post(self):
        data = request.get_json()
        try:
            UserSchema(only=("email", "password")).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()
        user = session.query(User).filter(User.email == data["email"]).first()
        if not user:
            raise errors.UserNotFoundError
        if not user.check_password(data["password"]):
            raise errors.WrongCredentialsError

        return jsonify(get_user_tokens(user.id))


api.add_resource(UserResource, "/users/<username>")
api.add_resource(UsersListResource, "/users")
api.add_resource(UserRegisterResource, "/register")
api.add_resource(UserLoginResource, "/login")
