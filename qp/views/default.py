from flask import Blueprint, render_template, make_response, redirect, url_for
from flask_babel import _
from flask_jwt_extended import jwt_required

from qp.api.models.users import Points

blueprint = Blueprint(
    "default",
    __name__,
)


@blueprint.route("/")
@jwt_required(optional=True)
def index():
    return redirect(url_for("polls.polls_list"))


@blueprint.route("/points")
@jwt_required(optional=True)
def points_info():
    title = _("Points")
    return render_template("points.html", title=title, points=Points)


@blueprint.route("/verification")
@jwt_required(optional=True)
def verification_info():
    title = _("Verification")
    return render_template("verification.html", title=title)


@blueprint.route("/change_language/<lang>")
@jwt_required(optional=True)
def change_language(lang):
    resp = make_response(redirect("/"))
    resp.set_cookie("language", lang)
    return resp
