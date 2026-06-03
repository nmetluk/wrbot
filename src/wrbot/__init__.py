"""
wrbot — Telegram бот для напоминаний о регулярных списаниях.

Бот помогает отслеживать recurring charges (подписки, кредиты, ЖКХ)
и присылать напоминания за N дней до списания.
"""

__version__ = "0.2.0"

from wrbot.logging import setup_logging

__all__ = ["__version__", "setup_logging"]
