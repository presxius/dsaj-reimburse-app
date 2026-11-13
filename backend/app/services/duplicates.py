"""Deteksi kemungkinan struk duplikat (PRD Future Improvements #5).

Hanya peringatan untuk admin/karyawan, bukan penolakan otomatis: transaksi kembar yang sah
(mis. dua kali naik taksi dengan tarif sama) tetap bisa diajukan.
"""
from sqlalchemy import and_, func, or_

from ..models import Receipt, Reimbursement, Status


def same_file(sha256, exclude_id=None):
    """Pengajuan (bukan draft) yang melampirkan file struk identik."""
    if not sha256:
        return []
    q = Reimbursement.query.filter(Reimbursement.status != Status.DRAFT,
                                   Reimbursement.receipt.has(Receipt.sha256 == sha256))
    if exclude_id:
        q = q.filter(Reimbursement.id != exclude_id)
    return q.order_by(Reimbursement.id).all()


def find_duplicates(r):
    """Kembalikan [(pengajuan_lain, alasan)], alasan: 'same_file' atau 'same_data'.

    'same_data' = kategori, tanggal, dan nominal sama, dari karyawan yang sama
    atau dengan merchant yang sama.
    """
    found = {d.id: (d, "same_file") for d in same_file(r.receipt.sha256 if r.receipt else None, r.id)}

    same_owner_or_merchant = [Reimbursement.employee_id == r.employee_id]
    if r.merchant:
        same_owner_or_merchant.append(func.lower(Reimbursement.merchant) == r.merchant.lower())
    similar = Reimbursement.query.filter(
        Reimbursement.id != r.id,
        Reimbursement.status != Status.DRAFT,
        and_(Reimbursement.category == r.category,
             Reimbursement.transaction_date == r.transaction_date,
             Reimbursement.amount == r.amount),
        or_(*same_owner_or_merchant),
    ).order_by(Reimbursement.id).all()
    for d in similar:
        found.setdefault(d.id, (d, "same_data"))
    return list(found.values())


def to_dict(r, reason):
    return {"id": r.id, "code": r.code, "status": r.status, "employee": r.employee.name,
            "transaction_date": r.transaction_date.isoformat(), "amount": float(r.amount),
            "reason": reason}
