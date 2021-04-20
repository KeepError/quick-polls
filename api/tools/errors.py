from flask import jsonify


class ApiError(Exception):
    status_code = 500
    sub_code = 0
    message = "Error."
    payload = None

    def __init__(self, payload=None):
        self.payload = payload

    def to_dict(self):
        data_error = {"code": self.sub_code}
        if self.payload:
            data_error.update(self.payload)
        return {"error": data_error, "message": self.message}

    def create_response(self):
        response = jsonify(self.to_dict())
        response.status_code = self.status_code
        return response

    @classmethod
    def sub_code_match(cls, sub_code):
        return cls.sub_code == sub_code

    def __repr__(self):
        return f"[{self.sub_code}] {self.__class__.__name__}: {self.message}"


class UnknownError(ApiError):
    status_code = 500
    sub_code = 1
    message = "Unknown error."


class DatabaseError(ApiError):
    status_code = 500
    sub_code = 2
    message = "Database error."


class InvalidRequestError(ApiError):
    status_code = 400
    sub_code = 3
    message = "Invalid request."

    def __init__(self, fields):
        super().__init__()
        self.payload = {"fields": fields}


class AccessDeniedError(ApiError):
    status_code = 403
    sub_code = 4
    message = "Access denied."


class UserBannedError(ApiError):
    status_code = 403
    sub_code = 5
    message = "You were banned."


class NoAuthError(ApiError):
    status_code = 401
    sub_code = 10
    message = "You are not authorized."


class UserNotFoundError(ApiError):
    status_code = 404
    sub_code = 100
    message = "User not found."


class UserAlreadyExistsError(ApiError):
    status_code = 404
    sub_code = 101
    message = "User already exists."


class WrongCredentialsError(ApiError):
    status_code = 404
    sub_code = 102
    message = "Wrong credentials."


class WrongOldPasswordError(ApiError):
    status_code = 404
    sub_code = 103
    message = "Old password is wrong."


class GroupNotFoundError(ApiError):
    status_code = 404
    sub_code = 104
    message = "Group not found."


class GroupNotAllowedError(ApiError):
    status_code = 403
    sub_code = 105
    message = "You cannot set this group."


class UnknownActionError(ApiError):
    status_code = 404
    sub_code = 106
    message = "Action not recognized."


class PollNotFoundError(ApiError):
    status_code = 404
    sub_code = 110
    message = "Poll not found."


class PollCompleted(ApiError):
    status_code = 403
    sub_code = 111
    message = "Poll has completed."


class NotEnoughPointsError(ApiError):
    status_code = 403
    sub_code = 119
    message = "Not enough points."


class OptionNotFoundError(ApiError):
    status_code = 404
    sub_code = 120
    message = "Option not found."
