import os

import click
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .extensions import db, migrate
from .utils.auth import load_current_user
from .utils.errors import ApiError


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("DATABASE_URL belum diisi (contoh: postgresql+psycopg://user:pass@localhost:5432/reimburse).")
    os.makedirs(os.path.dirname(app.config["UPLOAD_FOLDER"]), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    app.before_request(load_current_user)

    from .routes import admin, auth, receipts, reimbursements, reports
    for module in (auth, reimbursements, receipts, reports, admin):
        app.register_blueprint(module.bp)

    @app.errorhandler(ApiError)
    def handle_api_error(e):
        db.session.rollback()
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        db.session.rollback()
        messages = {404: "Endpoint tidak ditemukan.", 413: "Ukuran file terlalu besar.",
                    405: "Metode tidak diizinkan."}
        return jsonify({"error": messages.get(e.code, e.description)}), e.code

    @app.cli.command("seed")
    def seed():
        """Isi data contoh (dilewati bila sudah ada pengguna)."""
        from .seed import seed_data
        seed_data()
        click.echo("Seed selesai.")

    return app
