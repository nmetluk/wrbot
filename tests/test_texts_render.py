"""
Тест рендера текстов с подстановками.

Проверяет, что все строки с format() корректно рендерятся.
"""

import pytest

from wrbot.bot.texts import Texts


@pytest.mark.parametrize(
    ("template", "kwargs"),
    [
        # Кошельки
        (Texts.wallet_list_item, {"name": "Тинькофф"}),
        (Texts.wallet_added, {"name": "Наличные"}),
        (Texts.wallet_renamed, {"name": "Сбер"}),
        (Texts.wallet_deleted, {"name": "VTB"}),
        (Texts.wallet_enter_new_name, {"name": "Старое"}),
        (Texts.wallet_confirm_delete, {"name": "Тест"}),
        # Категории
        (Texts.category_list_item, {"name": "Подписки"}),
        (Texts.category_added, {"name": "ЖКХ"}),
        (Texts.category_renamed, {"name": "Кредиты"}),
        (Texts.category_deleted, {"name": "Еда"}),
        (Texts.category_enter_new_name, {"name": "Старая"}),
        (Texts.category_confirm_delete, {"name": "Тест"}),
        # Ошибки
        (Texts.error_name_too_long, {"max": 100}),
        (Texts.error_limit_exceeded, {"max": 10}),
        # M4 reminders (TASK-0015)
        (
            Texts.reminder_notification,
            {"name": "Тест", "amount": "1500.00", "wallet": "Тинькофф", "next_date": "2026-06-15"},
        ),
        (Texts.reminder_paid_periodic, {"next_date": "2026-07-15"}),
        # Глобальные уведомления (TASK-0026)
        (Texts.global_notify_current, {"time": "09:30", "days": "5, 3, 1"}),
        (Texts.global_notify_time_saved, {"time": "08:00"}),
        (Texts.global_days_edit_title, {"current": "5, 3, 1"}),
        # M7 formatters (TASK-0039)
        (Texts.notify_custom, {"days": "1, 3, 5"}),
        (
            Texts.my_charges_button,
            {"name": "VPN", "amount": "299.00", "wallet": "Сбер", "next_date": "15.07.2026"},
        ),
    ],
)
def test_text_template_renders(template, kwargs):
    """Все шаблоны текстов рендерятся без ошибок с корректными параметрами."""
    result = template.format(**kwargs)
    assert isinstance(result, str)
    assert len(result) > 0
    # Проверка, что подстановка действительно произошла
    for value in kwargs.values():
        assert str(value) in result or value in result


def test_wallet_added_render_real_example():
    """Реальный пример рендера текста добавления кошелька."""
    wallet_name = "Тинькофф Black"
    result = Texts.wallet_added.format(name=wallet_name)

    assert result == "✅ Кошелёк «Тинькофф Black» добавлен."
    assert "Тинькофф Black" in result
    assert "добавлен" in result


def test_category_renamed_render_real_example():
    """Реальный пример рендера текста переименования категории."""
    category_name = "Продукты"
    result = Texts.category_renamed.format(name=category_name)

    assert result == "✅ Категория переименована в «Продукты»."
    assert "Продукты" in result


def test_reminder_notification_render_real_example():
    """Реальный рендер текста уведомления (TASK-0015, переиспользуется в свипе 0016)."""
    result = Texts.reminder_notification.format(
        name="Оплата VPN",
        amount="299.00",
        wallet="Сбер",
        next_date="2026-06-10",
    )

    assert "🔔 *Напоминание о списании*" in result
    assert "Оплата VPN" in result
    assert "299.00 ₽" in result
    assert "Сбер" in result
    assert "2026-06-10" in result


def test_error_limit_exceeded_render_real_example():
    """Реальный пример рендера ошибки лимита."""
    limit = 15
    result = Texts.error_limit_exceeded.format(max=limit)

    assert result == f"❌ Превышен лимит (максимум {limit} шт.)."
    assert "15" in result
    assert "лимит" in result


def test_wallet_confirm_delete_render_real_example():
    """Реальный пример рендера подтверждения удаления кошелька."""
    wallet_name = "Мой кошелёк"
    result = Texts.wallet_confirm_delete.format(name=wallet_name)

    assert "Мой кошелёк" in result
    assert "удалить" in result
    assert "История списаний" in result


def test_global_notify_current_render_real_example():
    """Реальный рендер экрана глобальных уведомлений (TASK-0026)."""
    result = Texts.global_notify_current.format(time="10:00", days="5, 3, 1")
    assert "10:00" in result
    assert "5, 3, 1" in result
    assert "Глобальные уведомления" in result


def test_notify_custom_and_my_charges_button_render_real_example():
    """Реальный рендер форматтеров M7 (TASK-0039): без мока Texts, проверка подстановки."""
    custom = Texts.notify_custom.format(days="1, 15")
    assert custom == "свои: 1, 15"
    assert "свои: 1, 15" in custom

    button = Texts.my_charges_button.format(
        name="Оплата", amount="1200.00", wallet="Наличные", next_date="03.06.2026"
    )
    assert "Оплата" in button
    assert "1200.00 ₽ (Наличные)" in button
    assert "03.06.2026" in button
