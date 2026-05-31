# Документация wrbot

Карта документации. Начинать читать сверху вниз.

## Что за продукт
- [`spec/spec-v1.md`](spec/spec-v1.md) — **ТЗ v1.0** (исходное требование, неизменяемое).
- [`vision.md`](vision.md) — видение продукта и границы.
- [`requirements.md`](requirements.md) — структурированные функциональные (FR) и нефункциональные (NFR) требования с трассировкой к ТЗ.
- [`glossary.md`](glossary.md) — единый словарь терминов.

## Как мы строим
- [`architecture/`](architecture/) — обзор системы, модель данных, компоненты, журнал архитектурных решений (ADR).
- [`roadmap.md`](roadmap.md) — майлстоуны M0…M5 и точки обязательного аудита.

## Как мы работаем вместе
- [`workflow/`](workflow/) — протоколы и гайды ролей:
  - [`architect-guide.md`](workflow/architect-guide.md) — роль архитектора (cowork).
  - [`executor-guide.md`](workflow/executor-guide.md) — роль исполнителя (Claude Code).
  - [`handoff-protocol.md`](workflow/handoff-protocol.md) — контракт передачи задач.
  - [`session-protocol.md`](workflow/session-protocol.md) — жизненный цикл сессии.
  - [`context-preservation.md`](workflow/context-preservation.md) — как сохраняется контекст между сессиями.
  - [`audit-protocol.md`](workflow/audit-protocol.md) — аудит после каждого раздела.

## Шаблоны
- [`templates/`](templates/) — задача, отчёт, лог сессии, отчёт аудита, ADR.
