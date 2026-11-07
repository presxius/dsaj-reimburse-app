"""Aturan siapa boleh melihat pengajuan mana (Business Rules 5, 6, 15-17)."""
from ..models import ADMIN_CATEGORY, Reimbursement, Role, Status, User


def scoped_query(user):
    q = Reimbursement.query
    if user.role == Role.SUPER_ADMIN:
        return q
    if user.role == Role.EMPLOYEE:
        return q.filter(Reimbursement.employee_id == user.id)
    if user.role in ADMIN_CATEGORY:
        return q.filter(Reimbursement.category == ADMIN_CATEGORY[user.role],
                        Reimbursement.status != Status.DRAFT)
    if user.role == Role.APPROVER:
        return q.join(User, Reimbursement.employee_id == User.id).filter(
            User.approver_id == user.id,
            Reimbursement.status.notin_([Status.DRAFT, Status.SUBMITTED, Status.UNDER_REVIEW]),
        )
    if user.role == Role.FINANCE:
        return q.filter(Reimbursement.status.in_(Status.FINANCE_VISIBLE))
    return q.filter(False)


def can_view(user, r):
    if user.role == Role.SUPER_ADMIN:
        return True
    if user.role == Role.EMPLOYEE:
        return r.employee_id == user.id
    if user.role in ADMIN_CATEGORY:
        return r.category == ADMIN_CATEGORY[user.role] and r.status != Status.DRAFT
    if user.role == Role.APPROVER:
        # Atasan juga bisa melihat riwayat yang sudah lewat tahap approval.
        return r.employee.approver_id == user.id and r.status not in (
            Status.DRAFT, Status.SUBMITTED, Status.UNDER_REVIEW)
    if user.role == Role.FINANCE:
        return r.status in Status.FINANCE_VISIBLE
    return False
