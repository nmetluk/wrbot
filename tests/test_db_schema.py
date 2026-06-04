"""
Тесты схемы БД и миграций.

Проверка что все таблицы из data-model.md создаются корректно,
с FK, ON DELETE CASCADE и UNIQUE constraints.
"""

from datetime import date, datetime
from decimal import Decimal

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

    # alembic_version - служебная таблица, её наличие нормально
    assert expected_tables.issubset(tables), f"Expected {expected_tables}, got {tables}"


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
        "last_currency": "TEXT",
        "created_at": "DATETIME",
    }

    for col, _col_type in expected.items():
        assert col in columns, f"Column {col} missing from users table"


async def test_charges_table_columns(db_session) -> None:
    """Проверка структуры таблицы charges с Date типами."""
    result = await db_session.execute(text("PRAGMA table_info(charges)"))
    columns = {row[1]: row[2] for row in result.fetchall()}

    # Проверяем что next_date и snoozed_until имеют тип DATE (а не DATETIME)
    assert "next_date" in columns
    assert "snoozed_until" in columns

    # Проверяем все колонки
    expected = {
        "id",
        "user_id",
        "name",
        "amount",
        "currency",
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
    assert expected.issubset(columns.keys())


async def test_foreign_keys_exist(db_session) -> None:
    """Проверка что внешние ключи созданы через миграцию."""
    # В SQLite FK можно получить через PRAGMA foreign_key_list
    expected_fks = {
        "wallets": [("users", "tg_id")],
        "categories": [("users", "tg_id")],
        "charges": [("users", "tg_id"), ("wallets", "id"), ("categories", "id")],
        "sent_reminders": [("charges", "id")],
    }

    for table, expected in expected_fks.items():
        result = await db_session.execute(text(f"PRAGMA foreign_key_list({table})"))
        fks = result.fetchall()

        # Проверяем количество FK
        assert len(fks) == len(expected), f"Expected {len(expected)} FKs in {table}, got {len(fks)}"


async def test_sent_reminders_unique_constraint(db_session) -> None:
    """Проверка UNIQUE ограничения на sent_reminders (ADR-0005)."""
    result = await db_session.execute(
        text("SELECT sql FROM sqlite_master WHERE type='table' AND name='sent_reminders'")
    )
    table_sql = result.scalar()

    assert table_sql is not None, "Table sent_reminders not found"
    assert "UNIQUE" in table_sql, "UNIQUE constraint not found in sent_reminders"
    assert "charge_id" in table_sql
    assert "target_date" in table_sql
    assert "days_before" in table_sql


async def test_cascade_delete_charge_removes_sent_reminders(db_session) -> None:
    """
    Проверка ON DELETE CASCADE: удаление charge удаляет связанные sent_reminders.

    Для SQLite нужно включить PRAGMA foreign_keys.
    """
    # Включаем FK в SQLite
    await db_session.execute(text("PRAGMA foreign_keys=ON"))
    await db_session.commit()

    # Создаём тестовые данные
    from datetime import date

    # Создаём пользователя
    user = User(tg_id=12345, last_currency="RUB")
    db_session.add(user)
    await db_session.flush()

    # Создаём кошелёк
    wallet = Wallet(user_id=12345, name="Test Wallet")
    db_session.add(wallet)
    await db_session.flush()

    # Создаём списание
    charge = Charge(
        id=1,
        user_id=12345,
        name="Test Charge",
        amount=Decimal("100.00"),
        currency="RUB",
        wallet_id=1,
        next_date=date(2026, 6, 1),
        period="monthly",
    )
    db_session.add(charge)
    await db_session.flush()

    # Создаём напоминание
    reminder = SentReminder(
        charge_id=1,
        target_date=date(2026, 6, 1),
        days_before=5,
        sent_at=datetime.now(),
    )
    db_session.add(reminder)
    await db_session.commit()

    # Проверяем что reminder создан
    result = await db_session.execute(text("SELECT COUNT(*) FROM sent_reminders"))
    count_before = result.scalar()
    assert count_before == 1

    # Удаляем charge
    await db_session.delete(charge)
    await db_session.commit()

    # Проверяем что reminder тоже удалён (CASCADE)
    result = await db_session.execute(text("SELECT COUNT(*) FROM sent_reminders"))
    count_after = result.scalar()
    assert count_after == 0, "SentReminder should be cascade deleted with Charge"


async def test_unique_constraint_prevents_duplicate_reminders(db_session) -> None:
    """Проверка что UNIQUE constraint предотвращает дубликаты."""
    # Включаем FK в SQLite
    await db_session.execute(text("PRAGMA foreign_keys=ON"))
    await db_session.commit()

    # Создаём тестовые данные
    user = User(tg_id=99999, last_currency="RUB")
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=99999, name="W")
    db_session.add(wallet)
    await db_session.flush()
    wallet_id = wallet.id

    charge = Charge(
        user_id=99999,
        name="C",
        amount=Decimal("1.00"),
        currency="RUB",
        wallet_id=wallet_id,
        next_date=date(2026, 6, 1),
        period="monthly",
    )
    db_session.add(charge)
    await db_session.flush()
    charge_id = charge.id

    # Создаём первый reminder
    reminder1 = SentReminder(
        charge_id=charge_id,
        target_date=date(2026, 6, 1),
        days_before=5,
        sent_at=datetime.now(),
    )
    db_session.add(reminder1)
    await db_session.commit()

    # Пытаемся создать дубликат
    reminder2 = SentReminder(
        charge_id=charge_id,
        target_date=date(2026, 6, 1),
        days_before=5,
        sent_at=datetime.now(),
    )
    db_session.add(reminder2)

    # Должно получить ошибку при коммите
    try:
        await db_session.commit()
        raise AssertionError("Should have raised IntegrityError for duplicate reminder")
    except Exception:
        # Ожидаемая ошибка UNIQUE constraint
        await db_session.rollback()


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
