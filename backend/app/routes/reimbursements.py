from datetime import date
from decimal import Decimal

from flask import Blueprint, g, jsonify, request
from sqlalchemy import and_, or_

from ..extensions import db
from ..models import (MAX_ITEMS, MAX_RECEIPTS_PER_ITEM, Category, Receipt, Reimbursement,
                      ReimbursementItem, Role, Status, User)
from ..services import duplicates
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
    # Rentang tanggal: pengajuan yang punya minimal satu item di dalam rentang.
    date_cond = []
    if d := parse_date(args.get("date_from"), "tanggal awal"):
        date_cond.append(ReimbursementItem.transaction_date >= d)
    if d := parse_date(args.get("date_to"), "tanggal akhir"):
        date_cond.append(ReimbursementItem.transaction_date <= d)
    if date_cond:
        q = q.filter(Reimbursement.items.any(and_(*date_cond)))
    if term := (args.get("q") or "").strip():
        like = f"%{term}%"
        q = q.join(Reimbursement.employee).filter(or_(
            Reimbursement.code.ilike(like), Reimbursement.purpose.ilike(like), User.name.ilike(like),
            Reimbursement.items.any(or_(ReimbursementItem.merchant.ilike(like),
                                        ReimbursementItem.note.ilike(like)))))
    return q


def _get_visible(rid):
    r = db.session.get(Reimbursement, rid)
    if r is None or not can_view(g.user, r):
        raise ApiError("Pengajuan tidak ditemukan.", 404)
    return r


def _item_error(n, message):
    return ApiError(f"Item {n}: {message}")


def _parse_item(n, raw):
    if not isinstance(raw, dict):
        raise _item_error(n, "Format item tidak valid.")
    try:
        tx_date = parse_date(raw.get("transaction_date"), "tanggal transaksi")
        amount = parse_amount(raw.get("amount"))
    except ApiError as e:
        raise _item_error(n, e.message)
    if tx_date is None:
        raise _item_error(n, "Tanggal transaksi wajib diisi.")
    if tx_date > date.today():
        raise _item_error(n, "Tanggal transaksi tidak boleh di masa depan.")
    if amount is None:
        raise _item_error(n, "Nominal wajib diisi.")
    receipt_ids = raw.get("receipt_ids") or []
    if not isinstance(receipt_ids, list) or not all(isinstance(i, int) for i in receipt_ids):
        raise _item_error(n, "Daftar struk tidak valid.")
    if len(receipt_ids) > MAX_RECEIPTS_PER_ITEM:
        raise _item_error(n, f"Maksimal {MAX_RECEIPTS_PER_ITEM} file bukti per item.")
    return {
        "id": raw.get("id"),
        "merchant": (raw.get("merchant") or "").strip()[:200] or None,
        "transaction_date": tx_date,
        "amount": amount,
        "note": (raw.get("note") or "").strip() or None,
        "ocr_confirmed": bool(raw.get("ocr_confirmed")),
        "receipt_ids": receipt_ids,
    }


def _apply_form(r, data):
    category = data.get("category")
    if category not in Category.ALL:
        raise ApiError("Kategori harus transportasi atau konsumsi.")
    purpose = (data.get("purpose") or "").strip()
    if not purpose:
        raise ApiError("Keperluan pengajuan wajib diisi.")
    raw_items = data.get("items") or []
    if not isinstance(raw_items, list):
        raise ApiError("Format item tidak valid.")
    if len(raw_items) > MAX_ITEMS:
        raise ApiError(f"Maksimal {MAX_ITEMS} item per pengajuan.")
    parsed = [_parse_item(n, raw) for n, raw in enumerate(raw_items, 1)]

    # Struk yang dipakai: milik karyawan ini, dan belum terpasang ke pengajuan lain.
    all_ids = [i for p in parsed for i in p["receipt_ids"]]
    if len(all_ids) != len(set(all_ids)):
        raise ApiError("Satu file struk hanya boleh dipakai pada satu item.")
    receipts = {rc.id: rc for rc in Receipt.query.filter(Receipt.id.in_(all_ids))} if all_ids else {}
    for rid in all_ids:
        rc = receipts.get(rid)
        if (rc is None or rc.uploaded_by != g.user.id
                or (rc.item is not None and rc.item.reimbursement_id != r.id)):
            raise ApiError("Struk tidak valid.")

    existing = {item.id: item for item in r.items}
    items = []
    for n, p in enumerate(parsed, 1):
        if p["id"] is not None:
            item = existing.get(p["id"])
            if item is None:
                raise _item_error(n, "Item tidak ditemukan pada pengajuan ini.")
        else:
            item = ReimbursementItem()
        item.position = n - 1
        item.merchant, item.transaction_date, item.amount = p["merchant"], p["transaction_date"], p["amount"]
        item.note, item.ocr_confirmed = p["note"], p["ocr_confirmed"]
        items.append((item, [receipts[i] for i in p["receipt_ids"]]))

    # Struk yang tidak dipakai lagi tetap disimpan di storage, hanya dilepas dari item.
    for item in r.items:
        for rc in list(item.receipts):
            if rc.id not in receipts:
                rc.item = None
    r.category, r.purpose = category, purpose
    r.items = [item for item, _ in items]  # item yang tidak ada di payload ikut terhapus
    for item, item_receipts in items:
        item.receipts = item_receipts
    r.amount = sum((item.amount for item in r.items), Decimal("0"))


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


def _detail(r):
    data = r.to_dict(detail=True)
    data["actions"] = available_actions(g.user, r)
    # Hanya pengajuan yang boleh dilihat pengguna ini yang ditampilkan.
    data["duplicates"] = duplicates.find_duplicates(r, lambda other: can_view(g.user, other))
    return data


@bp.get("/<int:rid>")
@login_required
def get_reimbursement(rid):
    return jsonify(_detail(_get_visible(rid)))


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
    return jsonify(_detail(r))
