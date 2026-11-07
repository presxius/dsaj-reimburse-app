from functools import wraps

from flask import g, session

from ..extensions import db
from ..models import ActivityLog, User
from .errors import ApiError


def load_current_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id:
        user = db.session.get(User, user_id)
        if user and user.is_active:
            g.user = user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.user is None:
            raise ApiError("Silakan login terlebih dahulu.", 401)
        return view(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.user is None:
                raise ApiError("Silakan login terlebih dahulu.", 401)
            if g.user.role not in roles:
                raise ApiError("Anda tidak memiliki akses ke fitur ini.", 403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def log_activity(action, entity=None, entity_id=None, detail=None, user=None):
    actor = user or g.get("user")
    db.session.add(ActivityLog(
        user_id=actor.id if actor else None,
        action=action, entity=entity, entity_id=entity_id, detail=detail,
    ))
