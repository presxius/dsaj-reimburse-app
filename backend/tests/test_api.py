from datetime import timedelta
from decimal import Decimal

import app.routes.receipts as receipts_route
from app.extensions import db
from app.models import ActivityLog
from app.routes.auth import LOCKOUT_WINDOW, MAX_FAILED_LOGINS
from app.seed import DEMO_PASSWORD

from .conftest import PNG, new_submission, upload

PNG_OTHER = PNG + b"\x01"  # isi berbeda -> hash berbeda


def _login(app, email, password=DEMO_PASSWORD):
    return app.test_client().post("/api/auth/login", json={"email": email, "password": password})


# --- Autentikasi -------------------------------------------------------------------------

def test_logout_clears_session(login):
    emp = login("karyawan")
    assert emp.get("/api/auth/me").json["email"] == "karyawan@dsaj.co.id"
    assert emp.post("/api/auth/logout").status_code == 200
    assert emp.get("/api/auth/me").status_code == 401


def test_wrong_password_and_unknown_email(app):
    assert _login(app, "karyawan@dsaj.co.id", "salah").status_code == 401
    assert _login(app, "tidakada@dsaj.co.id").status_code == 401


def test_login_lockout_after_repeated_failures(app):
    email = "karyawan@dsaj.co.id"
    for _ in range(MAX_FAILED_LOGINS):
        assert _login(app, email, "salah").status_code == 401

    # Password benar pun ditolak selama terkunci.
    res = _login(app, email)
    assert res.status_code == 429
    assert 0 < int(res.headers["Retry-After"]) <= LOCKOUT_WINDOW.total_seconds()

    # Percobaan saat terkunci tidak dicatat sebagai kegagalan baru (kunci tidak diperpanjang).
    _login(app, email, "salah")
    failed = ActivityLog.query.filter_by(action="auth.login_failed", detail=email).all()
    assert len(failed) == MAX_FAILED_LOGINS

    # Akun lain tidak terpengaruh.
    assert _login(app, "karyawan2@dsaj.co.id").status_code == 200

    # Setelah jendela waktu lewat, login kembali bisa.
    for log in failed:
        log.created_at -= LOCKOUT_WINDOW + timedelta(seconds=1)
    db.session.commit()
    assert _login(app, email).status_code == 200


def test_lockout_is_case_insensitive(app):
    for _ in range(MAX_FAILED_LOGINS):
        _login(app, "Karyawan@DSAJ.co.id", "salah")
    assert _login(app, "karyawan@dsaj.co.id").status_code == 429


# --- Manajemen pengguna --------------------------------------------------------------------

def test_super_admin_manages_users(app, login):
    sa = login("superadmin")
    body = {"name": "Karyawan Baru", "email": "baru@dsaj.co.id", "role": "employee",
            "password": "rahasia123"}
    assert sa.post("/api/users", json={**body, "password": "pendek"}).status_code == 400
    assert sa.post("/api/users", json={**body, "role": "raja"}).status_code == 400
    created = sa.post("/api/users", json=body)
    assert created.status_code == 201
    assert sa.post("/api/users", json=body).status_code == 400  # email sudah dipakai

    assert _login(app, "baru@dsaj.co.id", "rahasia123").status_code == 200
    uid = created.json["id"]
    assert sa.patch(f"/api/users/{uid}", json={"is_active": False}).json["is_active"] is False
    assert _login(app, "baru@dsaj.co.id", "rahasia123").status_code == 403


def test_inactive_user_session_is_dropped(app, login):
    emp = login("karyawan")
    sa = login("superadmin")
    uid = emp.get("/api/auth/me").json["id"]
    sa.patch(f"/api/users/{uid}", json={"is_active": False})
    assert emp.get("/api/reimbursements").status_code == 401


def test_admin_endpoints_require_super_admin(login):
    for name in ("karyawan", "admin.transport", "atasan", "finance"):
        client = login(name)
        assert client.get("/api/users").status_code == 403
        assert client.get("/api/activity-logs").status_code == 403
        assert client.post("/api/departments", json={"name": "X"}).status_code == 403


def test_departments(login):
    sa = login("superadmin")
    assert sa.post("/api/departments", json={"name": ""}).status_code == 400
    assert sa.post("/api/departments", json={"name": "Marketing"}).status_code == 201
    assert sa.post("/api/departments", json={"name": "Marketing"}).status_code == 400
    assert "Marketing" in [d["name"] for d in sa.get("/api/departments").json]


# --- Laporan -------------------------------------------------------------------------------

def test_report_access_and_scope(login):
    emp = login("karyawan")
    new_submission(emp, category="transport")
    new_submission(emp, category="consumption")

    assert emp.get("/api/reports").status_code == 403
    assert login("atasan").get("/api/reports").status_code == 403

    rows = login("admin.transport").get("/api/reports").json["rows"]
    assert [r["category"] for r in rows] == ["transport"]
    assert len(login("superadmin").get("/api/reports").json["rows"]) == 2

    csv = login("admin.konsumsi").get("/api/reports/export?category=consumption")
    assert csv.status_code == 200
    assert csv.mimetype == "text/csv"
    assert csv.data.decode("utf-8-sig").splitlines()[0].startswith("Kode,Karyawan")


def test_report_rejects_bad_date_filter(login):
    assert login("finance").get("/api/reports?date_from=kemarin").status_code == 400


# --- Deteksi duplikat ----------------------------------------------------------------------

def _submit(client, content, **extra):
    receipt = upload(client, content=content).json
    body = {"category": "transport", "transaction_date": "2026-01-10", "amount": 50000,
            "description": "Taksi", "merchant": "Blue Taxi", "receipt_id": receipt["id"],
            "submit": True, **extra}
    return client.post("/api/reimbursements", json=body).json


def _dupes(client, rid):
    return {(d["code"], d["reason"]) for d in client.get(f"/api/reimbursements/{rid}").json["duplicates"]}


def test_same_receipt_file_is_flagged(login):
    emp = login("karyawan")
    first = _submit(emp, PNG)

    # Karyawan langsung diperingatkan saat mengunggah file yang sama.
    again = upload(emp, content=PNG).json
    assert [d["code"] for d in again["duplicates"]] == [first["code"]]
    assert upload(emp, content=PNG_OTHER).json["duplicates"] == []

    second = _submit(emp, PNG, transaction_date="2026-01-11", amount=12000)
    admin = login("admin.transport")
    assert _dupes(admin, second["id"]) == {(first["code"], "same_file")}
    assert _dupes(admin, first["id"]) == {(second["code"], "same_file")}


def test_same_transaction_data_is_flagged(login):
    emp = login("karyawan")
    first = _submit(emp, PNG)
    second = _submit(emp, PNG_OTHER)  # file beda, data sama
    assert _dupes(login("admin.transport"), second["id"]) == {(first["code"], "same_data")}

    # Beda nominal = bukan duplikat.
    third = _submit(emp, PNG_OTHER + b"\x02", amount=51000)
    assert _dupes(emp, third["id"]) == set()


def test_other_employee_same_merchant_is_flagged_but_hidden_from_employee(login):
    first = _submit(login("karyawan"), PNG)
    emp2 = login("karyawan2")
    # File sama milik karyawan lain tidak dibocorkan ke karyawan ini...
    assert upload(emp2, content=PNG).json["duplicates"] == []
    second = _submit(emp2, PNG_OTHER)
    assert _dupes(emp2, second["id"]) == set()
    # ...tetapi admin melihatnya (merchant, tanggal, dan nominal sama).
    assert _dupes(login("admin.transport"), second["id"]) == {(first["code"], "same_data")}

    # Karyawan berbeda dengan merchant berbeda dan file berbeda: tidak ditandai.
    third = _submit(emp2, PNG_OTHER + b"\x02", merchant="Taksi Lain")
    assert (first["code"], "same_data") not in _dupes(login("admin.transport"), third["id"])


def test_drafts_are_not_counted_as_duplicates(login):
    emp = login("karyawan")
    draft = _submit(emp, PNG, submit=False)
    submitted = _submit(emp, PNG)
    assert _dupes(emp, submitted["id"]) == set()
    assert (submitted["code"], "same_file") in _dupes(emp, draft["id"])


# --- Confidence OCR ------------------------------------------------------------------------

def test_ocr_confidence_is_returned(login, monkeypatch):
    monkeypatch.setattr(receipts_route, "run_ocr", lambda path, size: (
        ["KOPI SENJA", "TOTAL 55.000"],
        {"merchant": "KOPI SENJA", "transaction_date": None, "total_amount": Decimal("55000"),
         "confidence": {"merchant": 0.98, "total_amount": 0.71}}))
    emp = login("karyawan")
    scan = upload(emp, path="/api/ocr/scan").json
    assert scan["ocr"]["confidence"] == {"merchant": 0.98, "total_amount": 0.71}
    assert scan["duplicates"] == []
