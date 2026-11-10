from flask import Blueprint, current_app, g, jsonify, request, send_file

from ..extensions import db
from ..models import OcrResult, Receipt, Role, utcnow
from ..ocr import OcrUnavailable, run_ocr
from ..services.access import can_view
from ..services.receipts import receipt_path, store_receipt
from ..utils.auth import log_activity, login_required, roles_required
from ..utils.errors import ApiError

bp = Blueprint("receipts", __name__, url_prefix="/api")


@bp.post("/receipts")
@roles_required(Role.EMPLOYEE)
def upload_receipt():
    """Unggah struk tanpa OCR."""
    receipt = store_receipt(request.files.get("file"), g.user)
    log_activity("receipt.upload", "receipt", receipt.id)
    db.session.commit()
    return jsonify(receipt.to_dict()), 201


@bp.post("/ocr/scan")
@roles_required(Role.EMPLOYEE)
def ocr_scan():
    """Unggah struk lalu jalankan OCR. Hasilnya hanya draft untuk mengisi form."""
    receipt = store_receipt(request.files.get("file"), g.user)
    ocr = OcrResult(receipt=receipt, status="processing")
    db.session.add(ocr)
    db.session.commit()

    try:
        lines, fields = run_ocr(receipt_path(receipt), current_app.config["OCR_MODEL_SIZE"])
        ocr.raw_text = "\n".join(lines)
        ocr.merchant = fields["merchant"]
        ocr.transaction_date = fields["transaction_date"]
        ocr.total_amount = fields["total_amount"]
        ocr.status = "completed"
        if not lines:
            ocr.error = "Tidak ada teks yang terbaca pada gambar."
    except OcrUnavailable as e:
        ocr.status, ocr.error = "failed", str(e)
    except Exception:  # OCR gagal tidak boleh menghalangi pengajuan manual (FR-038)
        current_app.logger.exception("OCR gagal untuk receipt %s", receipt.id)
        ocr.status, ocr.error = "failed", "Gambar tidak dapat diproses OCR."
    ocr.processed_at = utcnow()
    log_activity("ocr.scan", "receipt", receipt.id, ocr.status)
    db.session.commit()
    return jsonify(receipt.to_dict()), 201


@bp.get("/receipts/<int:receipt_id>/file")
@login_required
def receipt_file(receipt_id):
    receipt = db.session.get(Receipt, receipt_id)
    if receipt is None:
        raise ApiError("Struk tidak ditemukan.", 404)
    allowed = receipt.uploaded_by == g.user.id or (
        receipt.reimbursement is not None and can_view(g.user, receipt.reimbursement))
    if not allowed:
        raise ApiError("Anda tidak berwenang melihat struk ini.", 403)
    return send_file(receipt_path(receipt), mimetype=receipt.file_type, max_age=0)
