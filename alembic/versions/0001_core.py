"""core accounting tables (accounts, ledger_entries, account_subconto)

Revision ID: 0001_core
Revises:
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False, unique=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("account_type", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("is_folder", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_accounts_id", "accounts", ["id"])
    op.create_index("ix_accounts_code", "accounts", ["code"])

    op.create_table(
        "account_subconto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("ref_type", sa.String(length=50), nullable=False),
    )
    op.create_index("ix_account_subconto_account_id", "account_subconto", ["account_id"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("period", sa.DateTime(), nullable=False),
        sa.Column("recorder_type", sa.String(length=50), nullable=False),
        sa.Column("recorder_id", sa.Integer(), nullable=False),
        sa.Column("account_dr_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("account_cr_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("subconto_dr_1", sa.Integer(), nullable=True),
        sa.Column("subconto_dr_2", sa.Integer(), nullable=True),
        sa.Column("subconto_dr_3", sa.Integer(), nullable=True),
        sa.Column("subconto_cr_1", sa.Integer(), nullable=True),
        sa.Column("subconto_cr_2", sa.Integer(), nullable=True),
        sa.Column("subconto_cr_3", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_ledger_entries_id", "ledger_entries", ["id"])
    op.create_index("ix_ledger_entries_period", "ledger_entries", ["period"])
    op.create_index("ix_ledger_entries_recorder_type", "ledger_entries", ["recorder_type"])
    op.create_index("ix_ledger_entries_recorder_id", "ledger_entries", ["recorder_id"])


def downgrade():
    op.drop_table("ledger_entries")
    op.drop_table("account_subconto")
    op.drop_table("accounts")
