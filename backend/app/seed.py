"""Data contoh untuk development. Password semua akun: password123"""
from .extensions import db
from .models import Department, Role, User

DEMO_PASSWORD = "password123"


def seed_data():
    if User.query.first():
        return
    ops = Department(name="Operasional")
    fin = Department(name="Keuangan")
    it = Department(name="IT")
    db.session.add_all([ops, fin, it])

    def user(name, email, role, dep, approver=None):
        u = User(name=name, email=email, role=role, department=dep, approver=approver)
        u.set_password(DEMO_PASSWORD)
        db.session.add(u)
        return u

    user("Super Admin", "superadmin@dsaj.co.id", Role.SUPER_ADMIN, it)
    atasan = user("Budi Atasan", "atasan@dsaj.co.id", Role.APPROVER, ops)
    user("Rina Karyawan", "karyawan@dsaj.co.id", Role.EMPLOYEE, ops, atasan)
    user("Andi Karyawan", "karyawan2@dsaj.co.id", Role.EMPLOYEE, ops, atasan)
    user("Tono Admin Transport", "admin.transport@dsaj.co.id", Role.ADMIN_TRANSPORT, ops)
    user("Sari Admin Konsumsi", "admin.konsumsi@dsaj.co.id", Role.ADMIN_CONSUMPTION, ops)
    user("Dewi Finance", "finance@dsaj.co.id", Role.FINANCE, fin)
    db.session.commit()
