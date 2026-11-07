import csv
import io
from datetime import date

from flask import Blueprint, Response, g, jsonify, request

from ..models import Reimbursement, Role
from ..services.access import scoped_query
from ..utils.auth import log_activity, login_required, roles_required
from ..extensions import db
from .reimbursements import apply_filters

bp = Blueprint("reports", __name__, url_prefix="/api")

REPORT_ROLES = (Role.ADMIN_TRANSPORT, Role.ADMIN_CONSUMPTION, Role.FINANCE, Role.SUPER_ADMIN)


def _summarize(items):
    by_status, by_category = {}, {}
    for r in items:
        for bucket, key in ((by_status, r.status), (by_category, r.category)):
            entry = bucket.setdefault(key, {"count": 0, "amount": 0.0})
            entry["count"] += 1
            entry["amount"] += float(r.amount)
    return {
        "total_count": len(items),
        "total_amount": sum(float(r.amount) for r in items),
        "by_status": by_status,
        "by_category": by_category,
    }


@bp.get("/dashboard")
@login_required
def dashboard():
    items = scoped_query(g.user).order_by(Reimbursement.created_at.desc()).all()
    data = _summarize(items)
    data["recent"] = [r.to_dict() for r in items[:5]]
    return jsonify(data)


def _report_items():
    q = apply_filters(scoped_query(g.user), request.args)
    return q.order_by(Reimbursement.transaction_date.desc()).all()


def _row(r):
    d = r.to_dict()
    p = r.payment
    d["payment_date"] = p.payment_date.isoformat() if p and p.payment_date else None
    d["payment_reference"] = p.reference if p else None
    return d


@bp.get("/reports")
@roles_required(*REPORT_ROLES)
def report():
    items = _report_items()
    return jsonify({"summary": _summarize(items), "rows": [_row(r) for r in items]})


@bp.get("/reports/export")
@roles_required(*REPORT_ROLES)
def export_report():
    items = _report_items()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Kode", "Karyawan", "Departemen", "Kategori", "Merchant", "Tanggal Transaksi",
                "Keterangan", "Nominal", "Status", "Tanggal Pembayaran", "Referensi Pembayaran"])
    for r in items:
        row = _row(r)
        w.writerow([row["code"], row["employee"]["name"], row["employee"]["department"] or "",
                    row["category"], row["merchant"] or "", row["transaction_date"],
                    row["description"], f"{row['amount']:.2f}", row["status"],
                    row["payment_date"] or "", row["payment_reference"] or ""])
    log_activity("report.export", detail=request.query_string.decode()[:500])
    db.session.commit()
    filename = f"laporan-reimburse-{date.today().isoformat()}.csv"
    # BOM agar Excel membaca UTF-8 dengan benar.
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})
