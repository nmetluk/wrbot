"""
Smoke test: проверка импорта пакета.
"""


def test_import_wrbot() -> None:
    """Проверка что пакет импортируется без ошибок."""
    import wrbot  # noqa: F401
    from wrbot.bot.handlers import start  # noqa: F401
    from wrbot.bot.keyboards import get_main_menu_keyboard  # noqa: F401
    from wrbot.bot.texts import Texts  # noqa: F401
    from wrbot.config import get_settings  # noqa: F401
    from wrbot.db.models import (  # noqa: F401
        Base,
        Category,
        Charge,
        SentReminder,
        User,
        Wallet,
    )
    from wrbot.logging import setup_logging  # noqa: F401
    from wrbot.models import (  # noqa: F401
        Category as DomainCategory,
    )
