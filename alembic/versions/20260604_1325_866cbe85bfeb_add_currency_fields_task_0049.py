"""add_currency_fields_task_0049

Revision ID: 866cbe85bfeb
Revises: 6428ace93f06
Create Date: 2026-06-04 13:25:00.000000+00:00

TASK-0049: charges.currency (NOT NULL, server_default RUB + backfill) + users.last_currency (nullable)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "866cbe85bfeb"
down_revision: Union[str, None] = "6428ace93f06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # charges.currency: String(3), NOT NULL, server_default='RUB' + explicit backfill (как TASK-0042)
    op.add_column(
        "charges",
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
    )
    op.execute("UPDATE charges SET currency = 'RUB' WHERE currency IS NULL OR currency = ''")

    # users.last_currency: nullable (для обратной совместимости со старыми пользователями), дефолт RUB на уровне кода
    op.add_column("users", sa.Column("last_currency", sa.String(length=3), nullable=True))
    # no backfill: None у старых = RUB в отображении/логике (get_default)


def downgrade() -> None:
    op.drop_column("users", "last_currency")
    op.drop_column("charges", "currency")
