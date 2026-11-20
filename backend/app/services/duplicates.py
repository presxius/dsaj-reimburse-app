"""Deteksi kemungkinan struk duplikat (PRD Future Improvements #5), per item pengeluaran.

Hanya peringatan untuk admin/karyawan, bukan penolakan otomatis: transaksi kembar yang sah
(mis. dua kali naik taksi dengan tarif sama) tetap bisa diajukan.
"""
from sqlalchemy import func, or_

from ..models import Receipt, Reimbursement, ReimbursementItem, Status


def _items_query():
    return ReimbursementItem.query.join(Reimbursement, ReimbursementItem.reimbursement_id == Reimbursement.id)


def same_file(sha256, exclude_item_id=None):
    """Item pada pengajuan (bukan draft) yang melampirkan file struk identik."""
    if not sha256:
        return []
    q = _items_query().filter(Reimbursement.status != Status.DRAFT,
                              ReimbursementItem.receipts.any(Receipt.sha256 == sha256))
    if exclude_item_id:
        q = q.filter(ReimbursementItem.id != exclude_item_id)
    return q.order_by(ReimbursementItem.id).all()


def _candidates(r, item):
    """Item lain (pengajuan bukan draft, atau item lain di pengajuan yang sama) yang mirip `item`.

    Kembalikan [(item_lain, alasan)], alasan: 'same_file' atau 'same_data'.
    'same_data' = kategori, tanggal, dan nominal sama, dari karyawan yang sama
    atau dengan merchant yang sama.
    """
    visible = or_(Reimbursement.status != Status.DRAFT, Reimbursement.id == r.id)
    found = {}

    hashes = [rc.sha256 for rc in item.receipts if rc.sha256]
    if hashes:
        for other in _items_query().filter(
                visible, ReimbursementItem.id != item.id,
                ReimbursementItem.receipts.any(Receipt.sha256.in_(hashes))).order_by(ReimbursementItem.id):
            found[other.id] = (other, "same_file")

    owner_or_merchant = [Reimbursement.employee_id == r.employee_id]
    if item.merchant:
        owner_or_merchant.append(func.lower(ReimbursementItem.merchant) == item.merchant.lower())
    for other in _items_query().filter(
            visible, ReimbursementItem.id != item.id,
            Reimbursement.category == r.category,
            ReimbursementItem.transaction_date == item.transaction_date,
            ReimbursementItem.amount == item.amount,
            or_(*owner_or_merchant)).order_by(ReimbursementItem.id):
        found.setdefault(other.id, (other, "same_data"))
    return list(found.values())


def find_duplicates(r, visible_to=lambda reimbursement: True):
    """{item_id: [match, ...]} untuk semua item pengajuan `r` yang punya kemungkinan duplikat."""
    result = {}
    for item in r.items:
        matches = [to_dict(other, reason, r) for other, reason in _candidates(r, item)
                   if other.reimbursement_id == r.id or visible_to(other.reimbursement)]
        if matches:
            result[item.id] = matches
    return result


def to_dict(item, reason, current=None):
    r = item.reimbursement
    return {"id": r.id, "code": r.code, "status": r.status, "employee": r.employee.name,
            "item_id": item.id, "merchant": item.merchant,
            "transaction_date": item.transaction_date.isoformat(), "amount": float(item.amount),
            "reason": reason, "same_claim": current is not None and r.id == current.id}
