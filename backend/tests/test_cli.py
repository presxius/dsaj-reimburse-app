from app.models import Role, User


def create_superadmin(app, email, password, name="Boss"):
    return app.test_cli_runner().invoke(
        args=["create-superadmin", "--email", email, "--name", name, "--password", password])


def test_create_superadmin(app):
    r = create_superadmin(app, " Boss@X.co ", "rahasia123")
    assert r.exit_code == 0, r.output
    user = User.query.filter_by(email="boss@x.co").one()
    assert user.role == Role.SUPER_ADMIN and user.check_password("rahasia123")


def test_create_superadmin_rejects_duplicate_email(app):
    create_superadmin(app, "boss@x.co", "rahasia123")
    r = create_superadmin(app, "boss@x.co", "rahasia123")
    assert r.exit_code != 0 and "sudah terdaftar" in r.output


def test_create_superadmin_rejects_short_password(app):
    r = create_superadmin(app, "y@x.co", "short")
    assert r.exit_code != 0 and "minimal 8" in r.output
