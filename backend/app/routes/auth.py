from flask import Blueprint, g, jsonify, request, session

from ..extensions import db
from ..models import User
from ..utils.auth import log_activity, login_required
from ..utils.errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(data.get("password") or ""):
        raise ApiError("Email atau password salah.", 401)
    if not user.is_active:
        raise ApiError("Akun Anda dinonaktifkan. Hubungi Super Admin.", 403)
    session.clear()
    session["user_id"] = user.id
    log_activity("auth.login", "user", user.id, user=user)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.post("/logout")
def logout():
    if g.user:
        log_activity("auth.logout", "user", g.user.id)
        db.session.commit()
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
@login_required
def me():
    return jsonify(g.user.to_dict())
