"""hash struk dan confidence ocr

Revision ID: b7c41e2d9f03
Revises: ea9083d2956a
Create Date: 2026-11-13 10:00:00.000000

"""
import hashlib
import os

from alembic import op
import sqlalchemy as sa
from flask import current_app


# revision identifiers, used by Alembic.
revision = 'b7c41e2d9f03'
down_revision = 'ea9083d2956a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('receipts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sha256', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_receipts_sha256'), ['sha256'], unique=False)

    with op.batch_alter_table('ocr_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confidence', sa.JSON(), nullable=True))

    # Isi hash untuk struk lama dari file di storage. File yang hilang dibiarkan tanpa hash.
    conn = op.get_bind()
    folder = current_app.config["UPLOAD_FOLDER"]
    for rid, key in conn.execute(sa.text("SELECT id, storage_key FROM receipts")).fetchall():
        try:
            with open(os.path.join(folder, key), "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            continue
        conn.execute(sa.text("UPDATE receipts SET sha256 = :h WHERE id = :id"), {"h": digest, "id": rid})


def downgrade():
    with op.batch_alter_table('ocr_results', schema=None) as batch_op:
        batch_op.drop_column('confidence')

    with op.batch_alter_table('receipts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_receipts_sha256'))
        batch_op.drop_column('sha256')
