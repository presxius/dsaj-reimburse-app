import os

import click
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .extensions import db
from .utils.auth import load_current_user
from .utils.errors import ApiError


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    os.makedirs(os.path.dirname(app.config["UPLOAD_FOLDER"]), exist_ok=True)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)
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

    @app.cli.command("init-db")
    @click.option("--seed/--no-seed", default=True, help="Isi data contoh.")
    def init_db(seed):
        """Buat tabel (dan data contoh)."""
        db.create_all()
        if seed:
            from .seed import seed_data
            seed_data()
        click.echo("Database siap.")

    return app
