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
        return jsonify({"error": e.message}), e.status, e.headers

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

    @app.cli.command("create-superadmin")
    @click.option("--email", prompt="Email")
    @click.option("--name", prompt="Nama", default="Super Admin")
    @click.password_option("--password", prompt="Password", confirmation_prompt="Ulangi password")
    def create_superadmin(email, name, password):
        """Buat akun Super Admin (untuk login pertama tanpa SEED_DEMO)."""
        from .models import Role, User
        email = email.strip().lower()
        if len(password) < 8:
            raise click.ClickException("Password minimal 8 karakter.")
        if User.query.filter_by(email=email).first():
            raise click.ClickException(f"Email {email} sudah terdaftar.")
        user = User(name=name.strip(), email=email, role=Role.SUPER_ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Super Admin {email} dibuat.")

    return app
