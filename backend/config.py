import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    # PostgreSQL, mis. postgresql+psycopg://user:pass@host:5432/reimburse (wajib diisi).
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # Koneksi PostgreSQL bisa putus saat idle; cek dulu sebelum dipakai.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "storage", "receipts"))
    MAX_RECEIPT_SIZE = int(os.environ.get("MAX_RECEIPT_SIZE", 5 * 1024 * 1024))  # 5 MB
    MAX_CONTENT_LENGTH = MAX_RECEIPT_SIZE + 1024 * 1024
    ALLOWED_RECEIPT_EXTENSIONS = {"jpg", "jpeg", "png"}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    # Ukuran model PP-OCRv6: tiny | small | medium. Makin besar makin akurat tapi butuh RAM
    # lebih banyak; "small" cukup untuk server ±1 GB RAM.
    OCR_MODEL_SIZE = os.environ.get("OCR_MODEL_SIZE", "small")


class TestConfig(Config):
    TESTING = True
    # Set TEST_DATABASE_URL untuk menjalankan test terhadap PostgreSQL.
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")
