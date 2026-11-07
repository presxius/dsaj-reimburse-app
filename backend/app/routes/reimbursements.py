from datetime import date

from flask import Blueprint, g, jsonify, request
from sqlalchemy import or_

from ..extensions import db
from ..models import Category, Receipt, Reimbursement, Role, Status, User
from ..services.access import can_view, scoped_query
from ..services.workflow import available_actions, transition
from ..utils.auth import log_activity, login_required, roles_required
from ..utils.errors import ApiError, parse_amount, parse_date

bp = Blueprint("reimbursements", __name__, url_prefix="/api/reimbursements")


def apply_filters(q, args):
    if args.get("status"):
        q = q.filter(Reimbursement.status.in_(args["status"].split(",")))
    if args.get("category"):
        q = q.filter(Reimbursement.category == args["category"])
    if d := parse_date(args.get("date_from"), "tanggal awal"):
        q = q.filter(Reimbursement.transaction_date >= d)
    if d := parse_date(args.get("date_to"), "tanggal akhir"):
        q = q.filter(Reimbursement.transaction_date <= d)
    if term := (args.get("q") or "").strip():
        like = f"%{term}%"
        q = q.join(Reimbursement.employee).filter(or_(
            Reimbursement.code.ilike(like), Reimbursement.merchant.ilike(like),
            Reimbursement.description.ilike(like), User.name.ilike(like)))
    return q


def _get_visible(rid):
    r = db.session.get(Reimbursement, rid)
    if r is None or not can_view(g.user, r):
        raise ApiError("Pengajuan tidak ditemukan.", 404)
    return r


def _apply_form(r, data):
    category = data.get("category")
    if category not in Category.ALL:
        raise ApiError("Kategori harus transportasi atau konsumsi.")
    tx_date = parse_date(data.get("transaction_date"), "tanggal transaksi")
    if tx_date is None:
        raise ApiError("Tanggal transaksi wajib diisi.")
    if tx_date > date.today():
        raise ApiError("Tanggal transaksi tidak boleh di masa depan.")
    amount = parse_amount(data.get("amount"))
    if amount is None:
        raise ApiError("Nominal wajib diisi.")
    description = (data.get("description") or "").strip()
    if not description:
        raise ApiError("Keterangan pengeluaran wajib diisi.")

    r.category, r.transaction_date, r.amount, r.description = category, tx_date, amount, description
    r.merchant = (data.get("merchant") or "").strip()[:200] or None

    receipt_id = data.get("receipt_id")
    if receipt_id and (r.receipt is None or r.receipt.id != receipt_id):
        receipt = db.session.get(Receipt, receipt_id)
        if receipt is None or receipt.uploaded_by != g.user.id or receipt.reimbursement_id is not None:
            raise ApiError("Struk tidak valid.")
        if r.receipt is not None:
            # Struk lama tetap disimpan di storage, hanya dilepas dari pengajuan.
            r.receipt.reimbursement_id = None
            db.session.flush()
        r.receipt = receipt


@bp.get("")
@login_required
def list_reimbursements():
    q = apply_filters(scoped_query(g.user), request.args)
    items = q.order_by(Reimbursement.created_at.desc()).limit(500).all()
    return jsonify([r.to_dict() for r in items])


@bp.post("")
@roles_required(Role.EMPLOYEE)
def create_reimbursement():
    data = request.get_json(silent=True) or {}
    r = Reimbursement(employee_id=g.user.id, status=Status.DRAFT)
    r.employee = g.user
    _apply_form(r, data)
    db.session.add(r)
    db.session.flush()
    r.code = f"RB-{r.created_at:%Y%m}-{r.id:05d}"
    log_activity("reimbursement.create", "reimbursement", r.id, r.code)
    if data.get("submit"):
        transition(g.user, r, "submit", data)  # commit di dalam
    else:
        db.session.commit()
    return jsonify(r.to_dict(detail=True)), 201


@bp.get("/<int:rid>")
@login_required
def get_reimbursement(rid):
    r = _get_visible(rid)
    data = r.to_dict(detail=True)
    data["actions"] = available_actions(g.user, r)
    return jsonify(data)


@bp.put("/<int:rid>")
@roles_required(Role.EMPLOYEE)
def update_reimbursement(rid):
    r = _get_visible(rid)
    if r.employee_id != g.user.id:
        raise ApiError("Pengajuan bukan milik Anda.", 403)
    if r.status not in Status.EDITABLE:
        raise ApiError("Pengajuan hanya bisa diubah saat Draft atau perlu revisi.", 409)
    data = request.get_json(silent=True) or {}
    _apply_form(r, data)
    log_activity("reimbursement.update", "reimbursement", r.id, r.code)
    if data.get("submit"):
        transition(g.user, r, "submit", data)
    else:
        db.session.commit()
    return jsonify(r.to_dict(detail=True))


@bp.post("/<int:rid>/actions/<action>")
@login_required
def do_action(rid, action):
    r = _get_visible(rid)
    transition(g.user, r, action, request.get_json(silent=True) or {})
    data = r.to_dict(detail=True)
    data["actions"] = available_actions(g.user, r)
    return jsonify(data)
