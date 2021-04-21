from flask_babel import _

from api.models import users

LANGUAGES = {
    "en": "English",
    "ru": "Русский"
}

GROUPS = {
    users.User: _("User"),
    users.ModeratorGroup: _("Moderator"),
    users.AdminGroup: _("Admin"),
    users.OwnerGroup: _("Owner")
}

INTERNAL_ERROR_MSG = _("Internal error. Try again.")
NO_RIGHTS_ERROR_MSG = _("You have no rights to do this.")
