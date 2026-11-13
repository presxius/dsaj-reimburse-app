import hashlib
import os
import uuid

from flask import current_app

from ..extensions import db
from ..models import Receipt
from ..utils.errors import ApiError

_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}


def _detect_mime(head):
    for sig, mime in _SIGNATURES.items():
        if head.startswith(sig):
            return mime
    return None


def store_receipt(file_storage, user):
    """Validasi ekstensi, isi file (magic bytes), dan ukuran, lalu simpan dengan nama acak."""
    if file_storage is None or not file_storage.filename:
        raise ApiError("File struk wajib diunggah.")

    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in current_app.config["ALLOWED_RECEIPT_EXTENSIONS"]:
        raise ApiError("Format file tidak didukung. Gunakan JPG, JPEG, atau PNG.")

    content = file_storage.read()
    max_size = current_app.config["MAX_RECEIPT_SIZE"]
    if len(content) == 0:
        raise ApiError("File kosong.")
    if len(content) > max_size:
        raise ApiError(f"Ukuran file melebihi batas {max_size // (1024 * 1024)} MB.")

    mime = _detect_mime(content[:8])
    if mime is None:
        raise ApiError("Isi file bukan gambar JPG/PNG yang valid.")

    storage_key = f"{uuid.uuid4().hex}.{'png' if mime == 'image/png' else 'jpg'}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, storage_key), "wb") as f:
        f.write(content)

    receipt = Receipt(original_filename=filename[:255], storage_key=storage_key, file_type=mime,
                      file_size=len(content), sha256=hashlib.sha256(content).hexdigest(),
                      uploaded_by=user.id)
    db.session.add(receipt)
    db.session.flush()
    return receipt


def receipt_path(receipt):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], receipt.storage_key)
