from datetime import date
from decimal import Decimal

import app.routes.receipts as receipts_route
from app.ocr import OcrUnavailable

from .conftest import PNG, new_submission, upload


def act(client, rid, action, **body):
    return client.post(f"/api/reimbursements/{rid}/actions/{action}", json=body)


def test_full_flow_to_paid(login):
    emp = login("karyawan")
    res = new_submission(emp)
    assert res.status_code == 201
    r = res.json
    assert r["status"] == "submitted" and r["code"].startswith("RB-")
    rid = r["id"]

    admin = login("admin.transport")
    assert [x["id"] for x in admin.get("/api/reimbursements").json] == [rid]
    assert act(admin, rid, "start_review").json["status"] == "under_review"
    assert act(admin, rid, "forward").json["status"] == "pending_approval"

    boss = login("atasan")
    assert act(boss, rid, "approve").json["status"] == "approved"

    fin = login("finance")
    assert act(fin, rid, "process_payment").json["status"] == "processing_payment"
    assert act(fin, rid, "mark_paid").status_code == 400  # tanggal & referensi wajib
    paid = act(fin, rid, "mark_paid", payment_date="2026-01-20", reference="TRF-001").json
    assert paid["status"] == "paid"
    assert paid["payment"]["reference"] == "TRF-001"

    detail = emp.get(f"/api/reimbursements/{rid}").json
    assert [h["to_status"] for h in detail["history"]] == [
        "submitted", "under_review", "pending_approval", "approved", "processing_payment", "paid"]

    report = fin.get("/api/reports").json
    assert report["summary"]["total_amount"] == 50000
    csv = fin.get("/api/reports/export")
    assert csv.status_code == 200 and b"TRF-001" in csv.data


def test_revision_cycle(login):
    emp = login("karyawan")
    rid = new_submission(emp).json["id"]
    admin = login("admin.transport")
    assert act(admin, rid, "admin_return").status_code == 400  # catatan wajib
    assert act(admin, rid, "admin_return", note="Struk buram").json["status"] == "revision_required"

    body = {"category": "transport", "transaction_date": "2026-01-10", "amount": 45000,
            "description": "Taksi (revisi)", "submit": True}
    res = emp.put(f"/api/reimbursements/{rid}", json=body)
    assert res.status_code == 200 and res.json["status"] == "submitted"
    assert emp.put(f"/api/reimbursements/{rid}", json=body).status_code == 409


def test_access_control(login):
    emp = login("karyawan")
    rid = new_submission(emp).json["id"]

    other = login("karyawan2")
    assert other.get(f"/api/reimbursements/{rid}").status_code == 404
    assert other.get("/api/reimbursements").json == []

    konsumsi = login("admin.konsumsi")
    assert konsumsi.get(f"/api/reimbursements/{rid}").status_code == 404
    assert act(konsumsi, rid, "forward").status_code == 404

    fin = login("finance")
    assert fin.get(f"/api/reimbursements/{rid}").status_code == 404

    # Atasan belum boleh bertindak sebelum lolos verifikasi admin (Business Rule 8).
    boss = login("atasan")
    assert act(boss, rid, "approve").status_code == 404

    receipt_id = emp.get(f"/api/reimbursements/{rid}").json["receipt"]["id"]
    assert other.get(f"/api/receipts/{receipt_id}/file").status_code == 403
    assert login("admin.transport").get(f"/api/receipts/{receipt_id}/file").status_code == 200

    assert emp.get("/api/users").status_code == 403
    assert login("superadmin").get(f"/api/reimbursements/{rid}").status_code == 200


def test_approver_must_be_direct_superior(app, login):
    from app.extensions import db
    from app.models import Role, User

    other_boss = User(name="Boss Lain", email="boss2@dsaj.co.id", role=Role.APPROVER)
    other_boss.set_password("password123")
    db.session.add(other_boss)
    db.session.commit()

    rid = new_submission(login("karyawan")).json["id"]
    act(login("admin.transport"), rid, "forward")
    assert act(login("boss2"), rid, "approve").status_code == 404
    assert act(login("atasan"), rid, "approver_reject").status_code == 400  # alasan wajib
    assert act(login("atasan"), rid, "approver_reject", note="Di luar kebijakan").json["status"] == "rejected"


def test_upload_validation(login):
    emp = login("karyawan")
    assert upload(emp, content=b"not an image", name="x.png").status_code == 400
    assert upload(emp, content=PNG, name="x.pdf").status_code == 400
    assert upload(emp, content=PNG, name="x.png").status_code == 201


def test_submit_requires_receipt_and_valid_fields(login):
    emp = login("karyawan")
    base = {"category": "consumption", "transaction_date": "2026-01-10", "amount": 10000,
            "description": "Makan siang"}
    assert emp.post("/api/reimbursements", json={**base, "submit": True}).status_code == 400
    assert emp.post("/api/reimbursements", json={**base, "amount": -5}).status_code == 400
    assert emp.post("/api/reimbursements", json={**base, "category": "hotel"}).status_code == 400
    draft = emp.post("/api/reimbursements", json=base)
    assert draft.status_code == 201 and draft.json["status"] == "draft"
    assert login("admin.konsumsi").get("/api/reimbursements").json == []  # draft tidak terlihat


def test_ocr_result_must_be_confirmed(login, monkeypatch):
    monkeypatch.setattr(receipts_route, "run_ocr", lambda path, lang: (
        ["KOPI SENJA", "TOTAL 55.000"],
        {"merchant": "KOPI SENJA", "transaction_date": None, "total_amount": Decimal("55000")}))
    emp = login("karyawan")
    scan = upload(emp, path="/api/ocr/scan").json
    assert scan["ocr"]["status"] == "completed"
    assert scan["ocr"]["total_amount"] == 55000 and scan["ocr"]["transaction_date"] is None

    body = {"category": "consumption", "transaction_date": "2026-01-10", "amount": 55000,
            "description": "Rapat", "merchant": "KOPI SENJA", "receipt_id": scan["id"], "submit": True}
    assert emp.post("/api/reimbursements", json=body).status_code == 400
    res = emp.post("/api/reimbursements", json={**body, "ocr_confirmed": True})
    assert res.status_code == 201
    assert res.json["ocr_confirmed"] is True
    assert res.json["ocr_corrected"] is True  # tanggal diisi manual


def test_ocr_unavailable_falls_back_to_manual(login, monkeypatch):
    def boom(path, lang):
        raise OcrUnavailable("PaddleOCR belum terpasang di server.")
    monkeypatch.setattr(receipts_route, "run_ocr", boom)
    emp = login("karyawan")
    scan = upload(emp, path="/api/ocr/scan").json
    assert scan["ocr"]["status"] == "failed"
    res = new_submission(emp, receipt_id=scan["id"])
    assert res.status_code == 201 and res.json["status"] == "submitted"


def test_future_date_rejected(login):
    emp = login("karyawan")
    future = date.today().replace(year=date.today().year + 1).isoformat()
    assert new_submission(emp, transaction_date=future).status_code == 400
