"""
Тесты для SentReminderRepository (TASK-0014).

Идемпотентность записи.
"""

from datetime import date

import pytest

from wrbot.repositories.sent_reminders import SentReminderRepository


@pytest.mark.asyncio
async def test_record_and_was_sent(async_session):
    repo = SentReminderRepository(async_session)

    charge_id = 999
    target = date(2026, 8, 15)
    days = 3

    # First time
    inserted = await repo.record(charge_id, target, days)
    assert inserted is True
    assert await repo.was_sent(charge_id, target, days) is True

    # Duplicate (idempotent)
    inserted2 = await repo.record(charge_id, target, days)
    assert inserted2 is False  # already sent


@pytest.mark.asyncio
async def test_was_sent_false_for_other(async_session):
    repo = SentReminderRepository(async_session)
    assert await repo.was_sent(1, date(2026, 1, 1), 5) is False
