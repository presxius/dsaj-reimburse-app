"""pengajuan multi item

Satu pengajuan kini berisi beberapa item (reimbursement_items); struk dipasang ke item.
Data lama dipindahkan: setiap pengajuan menjadi pengajuan dengan satu item, keterangannya
menjadi "keperluan", dan struknya dipasang ke item tersebut.

Revision ID: c5e2a7f1b8d4
Revises: b7c41e2d9f03
Create Date: 2026-11-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5e2a7f1b8d4'
down_revision = 'b7c41e2d9f03'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reimbursement_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reimbursement_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('merchant', sa.String(length=200), nullable=True),
    sa.Column('transaction_date', sa.Date(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('ocr_confirmed', sa.Boolean(), nullable=False),
    sa.Column('ocr_corrected', sa.Boolean(), nullable=False),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['reimbursement_id'], ['reimbursements.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reimbursement_items_reimbursement_id'), 'reimbursement_items', ['reimbursement_id'], unique=False)
    op.create_index(op.f('ix_reimbursement_items_transaction_date'), 'reimbursement_items', ['transaction_date'], unique=False)

    op.add_column('reimbursements', sa.Column('purpose', sa.Text(), nullable=True))
    op.add_column('receipts', sa.Column('item_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_receipts_item_id'), 'receipts', ['item_id'], unique=False)
    op.create_foreign_key(None, 'receipts', 'reimbursement_items', ['item_id'], ['id'])

    # Pindahkan data: satu item per pengajuan lama.
    op.execute("UPDATE reimbursements SET purpose = description")
    op.execute("""
        INSERT INTO reimbursement_items
            (reimbursement_id, position, merchant, transaction_date, amount, ocr_confirmed, ocr_corrected)
        SELECT id, 0, merchant, transaction_date, amount, ocr_confirmed, ocr_corrected FROM reimbursements
    """)
    op.execute("""
        UPDATE receipts SET item_id = (
            SELECT i.id FROM reimbursement_items i WHERE i.reimbursement_id = receipts.reimbursement_id)
        WHERE reimbursement_id IS NOT NULL
    """)

    op.alter_column('reimbursements', 'purpose', nullable=False)
    # Constraint unik & foreign key kolom ini ikut terhapus bersama kolomnya.
    op.drop_column('receipts', 'reimbursement_id')
    for column in ('merchant', 'transaction_date', 'description', 'ocr_confirmed', 'ocr_corrected'):
        op.drop_column('reimbursements', column)


def downgrade():
    """Kembali ke satu struk per pengajuan.

    Pengajuan multi-item diringkas: merchant & tanggal dari item pertama, nominal = total,
    dan hanya struk pertama item pertama yang tetap terpasang (struk lain dilepas, file tetap ada).
    Catatan item dan catatan revisi per item hilang.
    """
    op.add_column('reimbursements', sa.Column('merchant', sa.String(length=200), nullable=True))
    op.add_column('reimbursements', sa.Column('transaction_date', sa.Date(), nullable=True))
    op.add_column('reimbursements', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('reimbursements', sa.Column('ocr_confirmed', sa.Boolean(), nullable=True))
    op.add_column('reimbursements', sa.Column('ocr_corrected', sa.Boolean(), nullable=True))
    op.add_column('receipts', sa.Column('reimbursement_id', sa.Integer(), nullable=True))

    first_item = """(SELECT i.{col} FROM reimbursement_items i WHERE i.reimbursement_id = reimbursements.id
                     ORDER BY i.position, i.id LIMIT 1)"""
    op.execute(f"""
        UPDATE reimbursements SET
            description = purpose,
            merchant = {first_item.format(col='merchant')},
            transaction_date = COALESCE({first_item.format(col='transaction_date')}, CAST(created_at AS DATE)),
            ocr_confirmed = COALESCE({first_item.format(col='ocr_confirmed')}, FALSE),
            ocr_corrected = COALESCE({first_item.format(col='ocr_corrected')}, FALSE)
    """)
    op.execute("""
        UPDATE receipts SET reimbursement_id = i.reimbursement_id
        FROM reimbursement_items i
        WHERE receipts.item_id = i.id
          AND receipts.id = (
              SELECT rc.id FROM receipts rc JOIN reimbursement_items i2 ON rc.item_id = i2.id
              WHERE i2.reimbursement_id = i.reimbursement_id
              ORDER BY i2.position, i2.id, rc.id LIMIT 1)
    """)

    for column in ('transaction_date', 'description', 'ocr_confirmed', 'ocr_corrected'):
        op.alter_column('reimbursements', column, nullable=False)
    op.create_unique_constraint(None, 'receipts', ['reimbursement_id'])
    op.create_foreign_key(None, 'receipts', 'reimbursements', ['reimbursement_id'], ['id'])

    op.drop_constraint('receipts_item_id_fkey', 'receipts', type_='foreignkey')
    op.drop_index(op.f('ix_receipts_item_id'), table_name='receipts')
    op.drop_column('receipts', 'item_id')
    op.drop_column('reimbursements', 'purpose')
    op.drop_index(op.f('ix_reimbursement_items_transaction_date'), table_name='reimbursement_items')
    op.drop_index(op.f('ix_reimbursement_items_reimbursement_id'), table_name='reimbursement_items')
    op.drop_table('reimbursement_items')
