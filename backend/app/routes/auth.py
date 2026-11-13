from datetime import timedelta

from flask import Blueprint, g, jsonify, request, session

from ..extensions import db
from ..models import ActivityLog, User, utcnow
from ..utils.auth import log_activity, login_required
from ..utils.errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Akun dikunci sementara setelah MAX_FAILED_LOGINS kali gagal dalam LOCKOUT_WINDOW.
# Dicatat di activity_logs (bukan memori proses) agar berlaku di semua worker gunicorn.
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def _lockout_remaining(email):
    """Sisa waktu kunci dalam detik, atau 0 bila boleh mencoba login."""
    now = utcnow()
    failures = [t for (t,) in db.session.query(ActivityLog.created_at).filter(
        ActivityLog.action == "auth.login_failed", ActivityLog.detail == email,
        ActivityLog.created_at > now - LOCKOUT_WINDOW,
    ).order_by(ActivityLog.created_at)]
    if len(failures) < MAX_FAILED_LOGINS:
        return 0
    # Kunci terbuka saat jumlah kegagalan dalam jendela turun di bawah batas.
    unlock_at = failures[len(failures) - MAX_FAILED_LOGINS] + LOCKOUT_WINDOW
    return max(1, int((unlock_at - now).total_seconds()))


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if remaining := _lockout_remaining(email):
        # Percobaan saat terkunci tidak dihitung, supaya orang lain tidak bisa
        # memperpanjang kunci akun seseorang tanpa batas.
        minutes = -(-remaining // 60)
        raise ApiError(f"Terlalu banyak percobaan login. Coba lagi dalam {minutes} menit.", 429,
                       {"Retry-After": str(remaining)})
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(data.get("password") or ""):
        log_activity("auth.login_failed", "user", user.id if user else None, email[:120], user=user)
        db.session.commit()
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
