# Отчёт по TASK-0037

- **Исполнитель/сессия:** SESSION-2026-06-03-11
- **Дата:** 2026-06-03T07:00:00Z
- **Итоговый статус:** done

## Что сделано
Краткое резюме по пунктам критериев приёмки.

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| В «Мои списания» нет «Закрыть»; exit via «◀️ В меню» (shows main) + «➕ Новое». Other views (card etc) no dups/no orphans. | ✅ | Removed sole "❌ Закрыть" row from get_my_charges_keyboard(); list/edit flows use menu/back. |
| `cancel` (in create/edit dialogs) resets FSM, shows «Действие отменено» + main menu. | ✅ | Standardized charges_create cancel to action_cancelled + kb; fixed settings cancel_action/command (was missing kb, causing orphan text). |
| No screens with orphan message after close/cancel (no nav). | ✅ | All cancel paths now attach main_menu kb; improved name/amount prompts to carry cancel kb (was None). |
| E2E via dp.feed_update: list_charges → main_menu → main (4 btns); cancel creation dialog → «Действие отменено» + menu. | ✅ | Added in test_e2e_smoke.py (real feeds, no teleport); direct kb asserts; handler unit tests updated for new calls. |
| Весь CI зелёный. | ✅ | ruff/mypy/pytest(208)/alembic/validate all 0. |

## Как проверено
- Тесты: uv run pytest (full 208, e2e + settings handlers + smoke cover the flows)
- CI: exact commands from executor-guide + ci.yml (format/check, mypy, pytest, BOT_TOKEN=test alembic, validate)
- Ручная: inspected kb str, fed updates in e2e harness, verified no "Закрыть" in list, cancel returns menu.

## Затронутые файлы
- src/wrbot/bot/keyboards.py (remove close row from get_my_charges_keyboard)
- src/wrbot/bot/handlers/settings.py (cancel_action + cancel_command now return main kb; import)
- src/wrbot/bot/handlers/charges_create.py (cancel uses action_cancelled + kb; name/amount/edit prompts use cancel kb instead of None)
- tests/test_e2e_smoke.py (stricter kb assert no close; new E2E scenarios 10/11 for list-menu and cancel-dialog)
- tests/test_handlers_settings.py (update cancel asserts for reply_markup)

## Отклонения от задачи
- As bonus (fits "no orphan" + UX checklist): attached cancel kb to name/amount steps (was None; other flows like wallets already did). Improves "kb immediately", no scope creep.
- No change to texts.py (used existing action_cancelled; specific new_charge_cancelled left unused but harmless).
- No new ADR (simple UX consistency fix post-0036).

## Открытые вопросы / следующий шаг
- TASK-0037 done (low prio, for v0.2.0). M6 complete (0031-37 + hotfixes). Next: architect-led audit per roadmap + docs/roadmap.md.
- /take-task would find inbox empty now.

## Коммиты
- (will be) feat(ux): TASK-0037 — remove duplicate «Закрыть» from lists; «Отмена» only for dialogs w/ «Действие отменено» + menu (Task: TASK-0037)
