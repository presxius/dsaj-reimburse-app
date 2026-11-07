import io

import pytest

from app import create_app
from app.extensions import db
from app.seed import DEMO_PASSWORD, seed_data

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture
def app(tmp_path):
    app = create_app("config.TestConfig")
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    with app.app_context():
        db.create_all()
        seed_data()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def login(app):
    """login('karyawan') -> test client yang sudah login sebagai akun seed."""
    def _login(name):
        client = app.test_client()
        res = client.post("/api/auth/login",
                          json={"email": f"{name}@dsaj.co.id", "password": DEMO_PASSWORD})
        assert res.status_code == 200, res.json
        return client
    return _login


def upload(client, path="/api/receipts", content=PNG, name="struk.png"):
    return client.post(path, data={"file": (io.BytesIO(content), name)},
                       content_type="multipart/form-data")


def new_submission(client, category="transport", submit=True, **extra):
    receipt = upload(client).json
    body = {"category": category, "transaction_date": "2026-01-10", "amount": 50000,
            "description": "Taksi ke kantor klien", "merchant": "Blue Taxi",
            "receipt_id": receipt["id"], "submit": submit, **extra}
    return client.post("/api/reimbursements", json=body)
