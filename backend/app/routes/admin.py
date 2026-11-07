"""Fitur Super Admin: pengguna, departemen, log aktivitas."""
from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import ActivityLog, Department, Role, User
from ..utils.auth import log_activity, roles_required
from ..utils.errors import ApiError

bp = Blueprint("admin", __name__, url_prefix="/api")


def _apply_user(user, data, creating):
    if "name" in data or creating:
        name = (data.get("name") or "").strip()
        if not name:
            raise ApiError("Nama wajib diisi.")
        user.name = name
    if "email" in data or creating:
        email = (data.get("email") or "").strip().lower()
        if "@" not in email:
            raise ApiError("Email tidak valid.")
        other = User.query.filter_by(email=email).first()
        if other and other.id != user.id:
            raise ApiError("Email sudah digunakan.")
        user.email = email
    if "role" in data or creating:
        if data.get("role") not in Role.ALL:
            raise ApiError("Role tidak valid.")
        user.role = data["role"]
    if data.get("password"):
        if len(data["password"]) < 8:
            raise ApiError("Password minimal 8 karakter.")
        user.set_password(data["password"])
    elif creating:
        raise ApiError("Password wajib diisi.")
    if "department_id" in data:
        dep_id = data["department_id"] or None
        if dep_id and db.session.get(Department, dep_id) is None:
            raise ApiError("Departemen tidak ditemukan.")
        user.department_id = dep_id
    if "approver_id" in data:
        appr_id = data["approver_id"] or None
        if appr_id:
            appr = db.session.get(User, appr_id)
            if appr is None or appr.role != Role.APPROVER:
                raise ApiError("Atasan harus pengguna dengan role Atasan.")
            if appr.id == user.id:
                raise ApiError("Pengguna tidak bisa menjadi atasan dirinya sendiri.")
        user.approver_id = appr_id
    if "is_active" in data:
        user.is_active = bool(data["is_active"])


@bp.get("/users")
@roles_required(Role.SUPER_ADMIN)
def list_users():
    return jsonify([u.to_dict() for u in User.query.order_by(User.name).all()])


@bp.post("/users")
@roles_required(Role.SUPER_ADMIN)
def create_user():
    user = User()
    _apply_user(user, request.get_json(silent=True) or {}, creating=True)
    db.session.add(user)
    db.session.flush()
    log_activity("user.create", "user", user.id, f"{user.email} ({user.role})")
    db.session.commit()
    return jsonify(user.to_dict()), 201


@bp.patch("/users/<int:uid>")
@roles_required(Role.SUPER_ADMIN)
def update_user(uid):
    user = db.session.get(User, uid)
    if user is None:
        raise ApiError("Pengguna tidak ditemukan.", 404)
    data = request.get_json(silent=True) or {}
    _apply_user(user, data, creating=False)
    changed = ", ".join(k for k in data if k != "password") + (", password" if data.get("password") else "")
    log_activity("user.update", "user", user.id, changed)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.get("/departments")
@roles_required(Role.SUPER_ADMIN)
def list_departments():
    return jsonify([d.to_dict() for d in Department.query.order_by(Department.name).all()])


@bp.post("/departments")
@roles_required(Role.SUPER_ADMIN)
def create_department():
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if not name:
        raise ApiError("Nama departemen wajib diisi.")
    if Department.query.filter_by(name=name).first():
        raise ApiError("Departemen sudah ada.")
    dep = Department(name=name)
    db.session.add(dep)
    db.session.flush()
    log_activity("department.create", "department", dep.id, name)
    db.session.commit()
    return jsonify(dep.to_dict()), 201


@bp.get("/activity-logs")
@roles_required(Role.SUPER_ADMIN)
def activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.id.desc()).limit(300).all()
    return jsonify([l.to_dict() for l in logs])
