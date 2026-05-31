"""Initial schema: users, wallets, categories, charges, sent_reminders

Revision ID: 001
Revises:
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Таблица users
    op.create_table(
        "users",
        sa.Column("tg_id", sa.Integer(), nullable=False),
        sa.Column("notify_time", sa.Time(), nullable=False, server_default="10:00"),
        sa.Column("tz", sa.Text(), nullable=False, server_default="Europe/Moscow"),
        sa.Column("global_days", sa.Text(), nullable=False, server_default="[5,3,1]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("tg_id"),
    )
    op.create_index(op.f("ix_users_tg_id"), "users", ["tg_id"])

    # Таблица wallets
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
    )
    op.create_index(op.f("ix_wallets_user_id"), "wallets", ["user_id"])

    # Таблица categories
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
    )
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"])

    # Таблица charges
    op.create_table(
        "charges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("next_date", sa.DateTime(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("individual_days", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("snoozed_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
    )
    op.create_index(op.f("ix_charges_user_id"), "charges", ["user_id"])
    op.create_index(op.f("ix_charges_wallet_id"), "charges", ["wallet_id"])

    # Таблица sent_reminders
    op.create_table(
        "sent_reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("charge_id", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.DateTime(), nullable=False),
        sa.Column("days_before", sa.Integer(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["charge_id"], ["charges.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("charge_id", "target_date", "days_before", name="uq_reminder"),
    )
    op.create_index(op.f("ix_sent_reminders_charge_id"), "sent_reminders", ["charge_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sent_reminders_charge_id"), table_name="sent_reminders")
    op.drop_table("sent_reminders")

    op.drop_index(op.f("ix_charges_wallet_id"), table_name="charges")
    op.drop_index(op.f("ix_charges_user_id"), table_name="charges")
    op.drop_table("charges")

    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_table("categories")

    op.drop_index(op.f("ix_wallets_user_id"), table_name="wallets")
    op.drop_table("wallets")

    op.drop_index(op.f("ix_users_tg_id"), table_name="users")
    op.drop_table("users")
