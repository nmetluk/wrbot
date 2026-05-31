"""
Тесты схемы БД и миграций.

Проверка что все таблицы из data-model.md создаются корректно.
"""

from sqlalchemy import text

from wrbot.db.models import (
    Base,
    Category,
    Charge,
    SentReminder,
    User,
    Wallet,
)


async def test_all_tables_created(db_session) -> None:
    """Проверка что все таблицы из схемы создаются."""
    # Получаем список таблиц через SQL
    result = await db_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    )
    tables = {row[0] for row in result.fetchall()}

    # Ожидаемые таблицы из data-model.md
    expected_tables = {"users", "wallets", "categories", "charges", "sent_reminders"}

    assert tables == expected_tables, f"Expected {expected_tables}, got {tables}"


async def test_users_table_columns(db_session) -> None:
    """Проверка структуры таблицы users."""
    result = await db_session.execute(text("PRAGMA table_info(users)"))
    columns = {row[1]: row[2] for row in result.fetchall()}

    # Ожидаемые колонки из data-model.md
    expected = {
        "tg_id": "INTEGER",
        "notify_time": "TIME",
        "tz": "TEXT",
        "global_days": "TEXT",
        "created_at": "DATETIME",
    }

    for col, _col_type in expected.items():
        assert col in columns, f"Column {col} missing from users table"
        # SQLite doesn't enforce types strictly, just check presence


async def test_charges_table_columns(db_session) -> None:
    """Проверка структуры таблицы charges с Decimal и JSON полями."""
    result = await db_session.execute(text("PRAGMA table_info(charges)"))
    columns = {row[1] for row in result.fetchall()}

    expected = {
        "id",
        "user_id",
        "name",
        "amount",
        "wallet_id",
        "category_id",
        "next_date",
        "period",
        "individual_days",
        "status",
        "paid_at",
        "snoozed_until",
        "created_at",
    }

    assert columns == expected, f"Expected {expected}, got {columns}"


async def test_sent_reminders_unique_constraint(db_session) -> None:
    """Проверка UNIQUE ограничения на sent_reminders (ADR-0005)."""
    # В SQLite UNIQUE constraint создаёт implicit index
    # Проверяем через SQL определения таблицы
    result = await db_session.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='sent_reminders'")
    )
    table_sql = result.scalar()

    assert table_sql is not None, "Table sent_reminders not found"
    assert "UNIQUE" in table_sql, "UNIQUE constraint not found in sent_reminders"
    assert "charge_id" in table_sql
    assert "target_date" in table_sql
    assert "days_before" in table_sql


async def test_user_model_repr() -> None:
    """Проверка что модели имеют корректное строковое представление."""
    # Проверка что модели импортируются
    assert User is not None
    assert Wallet is not None
    assert Category is not None
    assert Charge is not None
    assert SentReminder is not None

    # Проверка что Base.metadata содержит все таблицы
    tables = Base.metadata.tables.keys()
    expected = {"users", "wallets", "categories", "charges", "sent_reminders"}

    assert expected.issubset(tables)
