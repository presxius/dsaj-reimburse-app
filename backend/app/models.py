from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Role:
    EMPLOYEE = "employee"
    ADMIN_TRANSPORT = "admin_transport"
    ADMIN_CONSUMPTION = "admin_consumption"
    APPROVER = "approver"
    FINANCE = "finance"
    SUPER_ADMIN = "super_admin"

    ALL = [EMPLOYEE, ADMIN_TRANSPORT, ADMIN_CONSUMPTION, APPROVER, FINANCE, SUPER_ADMIN]


class Category:
    TRANSPORT = "transport"
    CONSUMPTION = "consumption"

    ALL = [TRANSPORT, CONSUMPTION]


# Kategori yang menjadi kewenangan masing-masing admin.
ADMIN_CATEGORY = {
    Role.ADMIN_TRANSPORT: Category.TRANSPORT,
    Role.ADMIN_CONSUMPTION: Category.CONSUMPTION,
}


class Status:
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING_PAYMENT = "processing_payment"
    PAID = "paid"

    ALL = [DRAFT, SUBMITTED, UNDER_REVIEW, REVISION_REQUIRED, REJECTED,
           PENDING_APPROVAL, APPROVED, PROCESSING_PAYMENT, PAID]
    EDITABLE = [DRAFT, REVISION_REQUIRED]
    FINANCE_VISIBLE = [APPROVED, PROCESSING_PAYMENT, PAID]


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    department = db.relationship("Department")
    approver = db.relationship("User", remote_side=[id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department": self.department.to_dict() if self.department else None,
            "approver": {"id": self.approver.id, "name": self.approver.name} if self.approver else None,
            "is_active": self.is_active,
        }


class Reimbursement(db.Model):
    __tablename__ = "reimbursements"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(20), nullable=False, index=True)
    merchant = db.Column(db.String(200))
    transaction_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default=Status.DRAFT, index=True)
    # Penanda bahwa karyawan sudah meninjau hasil OCR, dan apakah ada koreksi.
    ocr_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    ocr_corrected = db.Column(db.Boolean, default=False, nullable=False)
    submitted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    employee = db.relationship("User", foreign_keys=[employee_id])
    receipt = db.relationship("Receipt", uselist=False, back_populates="reimbursement")
    history = db.relationship("Approval", order_by="Approval.id", back_populates="reimbursement")
    payment = db.relationship("Payment", uselist=False, back_populates="reimbursement")

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "code": self.code,
            "category": self.category,
            "merchant": self.merchant,
            "transaction_date": self.transaction_date.isoformat(),
            "description": self.description,
            "amount": float(self.amount),
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "created_at": self.created_at.isoformat(),
            "employee": {
                "id": self.employee.id,
                "name": self.employee.name,
                "department": self.employee.department.name if self.employee.department else None,
            },
        }
        if detail:
            data.update({
                "ocr_confirmed": self.ocr_confirmed,
                "ocr_corrected": self.ocr_corrected,
                "receipt": self.receipt.to_dict() if self.receipt else None,
                "history": [h.to_dict() for h in self.history],
                "payment": self.payment.to_dict() if self.payment else None,
            })
        return data


class Receipt(db.Model):
    __tablename__ = "receipts"
    id = db.Column(db.Integer, primary_key=True)
    # Kosong saat struk baru diunggah (mis. untuk OCR) dan belum menjadi bagian pengajuan.
    reimbursement_id = db.Column(db.Integer, db.ForeignKey("reimbursements.id"), unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(255), unique=True, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    # SHA-256 isi file, untuk mendeteksi struk yang sama diunggah lebih dari sekali.
    sha256 = db.Column(db.String(64), index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reimbursement = db.relationship("Reimbursement", back_populates="receipt")
    ocr_result = db.relationship("OcrResult", uselist=False, back_populates="receipt")

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "uploaded_at": self.uploaded_at.isoformat(),
            "ocr": self.ocr_result.to_dict() if self.ocr_result else None,
        }


class OcrResult(db.Model):
    __tablename__ = "ocr_results"
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey("receipts.id"), unique=True, nullable=False)
    merchant = db.Column(db.String(200))
    transaction_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(14, 2))
    raw_text = db.Column(db.Text)
    # Skor keyakinan OCR (0-1) per field: {"merchant": 0.97, "transaction_date": ..., "total_amount": ...}.
    confidence = db.Column(db.JSON)
    status = db.Column(db.String(20), nullable=False, default="queued")  # queued|processing|completed|failed
    error = db.Column(db.String(255))
    processed_at = db.Column(db.DateTime)

    receipt = db.relationship("Receipt", back_populates="ocr_result")

    def to_dict(self):
        return {
            "status": self.status,
            "merchant": self.merchant,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "total_amount": float(self.total_amount) if self.total_amount is not None else None,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "error": self.error,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class Approval(db.Model):
    """Riwayat setiap perubahan status (verifikasi, persetujuan, pembayaran)."""
    __tablename__ = "approvals"
    id = db.Column(db.Integer, primary_key=True)
    reimbursement_id = db.Column(db.Integer, db.ForeignKey("reimbursements.id"), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(30), nullable=False)
    from_status = db.Column(db.String(30))
    to_status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reimbursement = db.relationship("Reimbursement", back_populates="history")
    actor = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "note": self.note,
            "actor": {"id": self.actor.id, "name": self.actor.name, "role": self.actor.role},
            "created_at": self.created_at.isoformat(),
        }


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    reimbursement_id = db.Column(db.Integer, db.ForeignKey("reimbursements.id"), unique=True, nullable=False)
    amount = db.Column(db.Numeric(14, 2))
    payment_date = db.Column(db.Date)
    reference = db.Column(db.String(120))
    status = db.Column(db.String(20), nullable=False)  # processing|paid
    processed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    reimbursement = db.relationship("Reimbursement", back_populates="payment")
    processor = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "amount": float(self.amount) if self.amount is not None else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "reference": self.reference,
            "status": self.status,
            "processed_by": self.processor.name,
        }


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.name if self.user else None,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "detail": self.detail,
            "created_at": self.created_at.isoformat(),
        }
