import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "reimburse.db")
    )
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "storage", "receipts"))
    MAX_RECEIPT_SIZE = int(os.environ.get("MAX_RECEIPT_SIZE", 5 * 1024 * 1024))  # 5 MB
    MAX_CONTENT_LENGTH = MAX_RECEIPT_SIZE + 1024 * 1024
    ALLOWED_RECEIPT_EXTENSIONS = {"jpg", "jpeg", "png"}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    # Bahasa model PaddleOCR. "en" cukup untuk struk berhuruf latin.
    OCR_LANG = os.environ.get("OCR_LANG", "en")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
