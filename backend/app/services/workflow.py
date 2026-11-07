"""Mesin status pengajuan reimburse (PRD bagian 7 & 8)."""
from ..extensions import db
from ..models import ADMIN_CATEGORY, Approval, Payment, Role, Status, utcnow
from ..utils.auth import log_activity
from ..utils.errors import ApiError, parse_amount, parse_date

S = Status

# action -> (role yang boleh, status asal yang diizinkan, status tujuan, catatan wajib?)
TRANSITIONS = {
    "submit":       ({Role.EMPLOYEE}, S.EDITABLE, S.SUBMITTED, False),
    "start_review": (set(ADMIN_CATEGORY), [S.SUBMITTED], S.UNDER_REVIEW, False),
    "forward":      (set(ADMIN_CATEGORY), [S.SUBMITTED, S.UNDER_REVIEW], S.PENDING_APPROVAL, False),
    "admin_return": (set(ADMIN_CATEGORY), [S.SUBMITTED, S.UNDER_REVIEW], S.REVISION_REQUIRED, True),
    "admin_reject": (set(ADMIN_CATEGORY), [S.SUBMITTED, S.UNDER_REVIEW], S.REJECTED, True),
    "approve":      ({Role.APPROVER}, [S.PENDING_APPROVAL], S.APPROVED, False),
    "approver_return": ({Role.APPROVER}, [S.PENDING_APPROVAL], S.REVISION_REQUIRED, True),
    "approver_reject": ({Role.APPROVER}, [S.PENDING_APPROVAL], S.REJECTED, True),
    "process_payment": ({Role.FINANCE}, [S.APPROVED], S.PROCESSING_PAYMENT, False),
    "mark_paid":    ({Role.FINANCE}, [S.PROCESSING_PAYMENT], S.PAID, False),
}


def _check_actor(user, r, action):
    roles = TRANSITIONS[action][0]
    if user.role not in roles:
        raise ApiError("Anda tidak berwenang melakukan tindakan ini.", 403)
    if user.role == Role.EMPLOYEE and r.employee_id != user.id:
        raise ApiError("Pengajuan bukan milik Anda.", 403)
    if user.role in ADMIN_CATEGORY and r.category != ADMIN_CATEGORY[user.role]:
        raise ApiError("Kategori pengajuan di luar kewenangan Anda.", 403)
    if user.role == Role.APPROVER and r.employee.approver_id != user.id:
        raise ApiError("Anda bukan atasan dari karyawan ini.", 403)


def available_actions(user, r):
    actions = []
    for name, (roles, sources, _, _) in TRANSITIONS.items():
        if r.status not in sources:
            continue
        try:
            _check_actor(user, r, name)
        except ApiError:
            continue
        actions.append(name)
    return actions


def transition(user, r, action, data):
    if action not in TRANSITIONS:
        raise ApiError("Tindakan tidak dikenal.")
    _, sources, target, note_required = TRANSITIONS[action]
    _check_actor(user, r, action)
    if r.status not in sources:
        raise ApiError(f"Tindakan tidak dapat dilakukan pada status '{r.status}'.", 409)

    note = (data.get("note") or "").strip() or None
    if note_required and not note:
        raise ApiError("Alasan / catatan wajib diisi.")

    if action == "submit":
        _validate_before_submit(r, data)
        r.submitted_at = utcnow()
    elif action == "process_payment":
        db.session.add(Payment(reimbursement=r, status="processing", processed_by=user.id,
                               amount=r.amount))
    elif action == "mark_paid":
        payment_date = parse_date(data.get("payment_date"), "tanggal pembayaran")
        reference = (data.get("reference") or "").strip()
        if not payment_date or not reference:
            raise ApiError("Tanggal dan referensi pembayaran wajib diisi.")
        amount = parse_amount(data.get("amount"), "nominal pembayaran") or r.amount
        p = r.payment
        p.payment_date, p.reference, p.amount = payment_date, reference, amount
        p.status, p.processed_by = "paid", user.id

    from_status = r.status
    r.status = target
    db.session.add(Approval(reimbursement=r, actor_id=user.id, action=action,
                            from_status=from_status, to_status=target, note=note))
    log_activity(f"reimbursement.{action}", "reimbursement", r.id,
                 f"{r.code}: {from_status} -> {target}")
    db.session.commit()
    return r


def _validate_before_submit(r, data):
    if r.receipt is None:
        raise ApiError("Bukti transaksi wajib dilampirkan.")
    ocr = r.receipt.ocr_result
    # Business Rule 19: hasil OCR wajib dikonfirmasi karyawan sebelum dikirim.
    if ocr and ocr.status == "completed":
        if not data.get("ocr_confirmed"):
            raise ApiError("Konfirmasi bahwa Anda sudah memeriksa hasil OCR terhadap struk asli.")
        r.ocr_confirmed = True
        r.ocr_corrected = (
            (ocr.merchant or None) != (r.merchant or None)
            or ocr.transaction_date != r.transaction_date
            or ocr.total_amount != r.amount
        )
