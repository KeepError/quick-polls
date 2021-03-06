from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import create_access_token, create_refresh_token, current_user
from flask_restful import Api, Resource
from marshmallow.exceptions import ValidationError
from sqlalchemy import desc

from qp import mail
from ..database import db_session
from ..models.polls import Poll
from ..models.users import User, generate_password, ModeratorGroup, get_group
from ..schemas.polls import PollSchema
from ..schemas.users import UserSchema, UserChangePasswordSchema, UserChangePointsSchema, CustomEmailSchema
from ..tools import errors
from ..tools.decorators import guest_required, user_required, moderator_required, admin_required
from ..tools.response import make_success_message
from ..tools.mail import MessageGenerator

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
    @guest_required()
    def get(self, username):
        exclude = ["email"]
        if current_user and (current_user.username == username or ModeratorGroup.is_belong(current_user.group)):
            exclude = []

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError
        data = UserSchema(exclude=exclude).dump(user)
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
    @moderator_required()
    def get(self):
        session = db_session.create_session()
        users = session.query(User).order_by(User.created_at.desc()).all()
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


class UserProfileResource(Resource):
    @user_required()
    def put(self, username):
        if current_user.username != username and not ModeratorGroup.is_belong(current_user.group):
            raise errors.AccessDeniedError

        data = request.get_json()
        try:
            UserSchema(only=("username", "bio", "avatar_filename")).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        if "avatar_filename" in data and not data.get("avatar_filename", None):
            data.pop("avatar_filename")

        session.query(User).filter(User.username == username).update(data)
        session.commit()
        return make_success_message()


class UserEmailResource(Resource):
    @user_required()
    def put(self, username):
        if current_user.username != username:
            raise errors.AccessDeniedError

        data = request.get_json()
        try:
            UserSchema(only=("email",)).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        data["email_confirmed"] = False
        session.query(User).filter(User.username == username).update(data)
        session.commit()
        return make_success_message()


class UserChangePasswordResource(Resource):
    @user_required()
    def put(self, username):
        if current_user.username != username:
            raise errors.AccessDeniedError

        data = request.get_json()
        try:
            UserChangePasswordSchema(exclude=("token",)).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        if not user.check_password(data["old_password"]):
            raise errors.WrongOldPasswordError

        user.set_password(data["new_password"])

        session.commit()
        return make_success_message()


class UserVerifyResource(Resource):
    @admin_required()
    def put(self, username):
        session = db_session.create_session()

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        user.verified = True
        session.commit()

        return make_success_message()


class UserCancelVerificationResource(Resource):
    @admin_required()
    def put(self, username):
        session = db_session.create_session()

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        user.verified = False
        session.commit()

        return make_success_message()


class UserBanResource(Resource):
    @moderator_required()
    def put(self, username):
        session = db_session.create_session()

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        if current_user.group <= user.group:
            raise errors.AccessDeniedError

        user.banned = True
        session.commit()

        return make_success_message()


class UserUnbanResource(Resource):
    @moderator_required()
    def put(self, username):
        session = db_session.create_session()

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        if current_user.group <= user.group:
            raise errors.AccessDeniedError

        user.banned = False
        session.commit()

        return make_success_message()


class UserChangeGroupResource(Resource):
    @admin_required()
    def put(self, username):
        data = request.get_json()
        try:
            UserSchema(only=("group",)).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        group_id = data["group"]
        if not get_group(id=group_id):
            raise errors.GroupNotFoundError
        if not current_user.group > group_id:
            raise errors.GroupNotAllowedError

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        if not current_user.group > user.group:
            raise errors.AccessDeniedError

        user.group = group_id

        session.commit()
        return make_success_message()


class UserChangePointsResource(Resource):
    @moderator_required()
    def put(self, username):
        data = request.get_json()
        try:
            UserChangePointsSchema().load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        if data["action"] not in (-1, 1):
            raise errors.UnknownActionError

        session = db_session.create_session()
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        user.points += data["action"] * data["count"]

        session.commit()
        return make_success_message()


class UserPollsResource(Resource):
    @user_required()
    def get(self, username):
        if not (current_user.username == username or ModeratorGroup.is_belong(current_user.group)):
            raise errors.AccessDeniedError

        session = db_session.create_session()

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        polls = session.query(Poll).filter(Poll.author_id == user.id).order_by(desc(Poll.created_at)).all()
        return jsonify({
            "polls": PollSchema().dump(polls, many=True)
        })


class SendCustomEmailResource(Resource):
    @admin_required()
    def post(self, username):
        data = request.get_json()
        try:
            CustomEmailSchema().load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise errors.UserNotFoundError

        try:
            mail.send(MessageGenerator(user.email).custom(**data))
        except Exception as e:
            raise errors.SendingEmailError

        return make_success_message()


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

        token = User.get_email_confirmation_token(user.id)
        try:
            mail.send(MessageGenerator(user.email).welcome(user, token))
        except Exception as e:
            pass

        return make_success_message()


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


class UserSendResetPasswordEmailResource(Resource):
    def post(self):
        data = request.get_json()
        try:
            UserSchema(only=("email",)).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        session = db_session.create_session()
        user = session.query(User).filter(User.email == data["email"]).first()
        if not user:
            raise errors.UserNotFoundError

        token = User.get_reset_token(user.id)
        try:
            mail.send(MessageGenerator(user.email).reset_password(user, token))
        except Exception as e:
            raise errors.SendingEmailError

        return make_success_message()


class UserResetPasswordResource(Resource):
    def post(self):
        data = request.get_json()
        try:
            UserChangePasswordSchema(exclude=("old_password",)).load(data)
        except ValidationError as e:
            raise errors.InvalidRequestError(e.messages)

        user_id = User.get_reset_token_info(data.get("token", None))
        if not user_id:
            raise errors.InvalidResetPasswordTokenError

        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise errors.UserNotFoundError

        user.set_password(data["new_password"])
        session.commit()

        return make_success_message()


class UserSendConfirmationEmailResource(Resource):
    @user_required()
    def post(self):
        user = current_user
        if user.email_confirmed:
            raise errors.EmailAlreadyConfirmedError

        token = User.get_email_confirmation_token(user.id)
        try:
            mail.send(MessageGenerator(user.email).confirm_email(user, token))
        except Exception as e:
            raise errors.SendingEmailError

        return make_success_message()


class UserConfirmEmailResource(Resource):
    def post(self):
        data = request.get_json()

        user_id = User.get_email_confirmation_token_info(data.get("token", None))
        if not user_id:
            raise errors.InvalidResetPasswordTokenError

        session = db_session.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise errors.UserNotFoundError

        user.email_confirmed = True
        session.commit()

        return make_success_message()


api.add_resource(UserResource, "/users/<username>")
api.add_resource(UsersListResource, "/users")
api.add_resource(UserProfileResource, "/users/<username>/profile")
api.add_resource(UserEmailResource, "/users/<username>/email")
api.add_resource(UserChangePasswordResource, "/users/<username>/change_password")
api.add_resource(UserVerifyResource, "/users/<username>/verify")
api.add_resource(UserCancelVerificationResource, "/users/<username>/cancel_verification")
api.add_resource(UserBanResource, "/users/<username>/ban")
api.add_resource(UserUnbanResource, "/users/<username>/unban")
api.add_resource(UserChangeGroupResource, "/users/<username>/change_group")
api.add_resource(UserChangePointsResource, "/users/<username>/change_points")
api.add_resource(UserPollsResource, "/users/<username>/polls")
api.add_resource(SendCustomEmailResource, "/users/<username>/send_email")
api.add_resource(UserRegisterResource, "/register")
api.add_resource(UserLoginResource, "/login")
api.add_resource(UserSendResetPasswordEmailResource, "/send_reset_password_email")
api.add_resource(UserResetPasswordResource, "/reset_password")
api.add_resource(UserSendConfirmationEmailResource, "/send_confirmation_email")
api.add_resource(UserConfirmEmailResource, "/confirm_email")
