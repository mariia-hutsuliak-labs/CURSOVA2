---
owner: Mariia Hutsuliak
status: published
review_date: 2027-05-13
---

# Реєстр архітектурних рішень (ADR)

ADR (Architecture Decision Record) фіксує одне архітектурне рішення: контекст, альтернативи, рішення і наслідки.

## Правила ведення

1. **Наскрізна нумерація.** Номери `0001`, `0002`, ... видаються по черзі й ніколи не перевикористовуються.
2. **Життєвий цикл статусу:** Proposed (запропоновано) → Accepted (прийнято) → Superseded (замінено).
3. **Незмінюваність.** Текст прийнятого ADR не редагується. Якщо рішення змінилося, створюється новий ADR, а в старому змінюється лише рядок статусу на `Superseded by ADR-XXXX`.
4. **Зв'язність.** Кожен ADR посилається на пов'язані рішення й документи (SDD, ISD).

## Реєстр

| № | Рішення | Статус | Дата |
|---|---|---|---|
| [0001](0001-postgresql-as-primary-store.md) | PostgreSQL як основне сховище даних | Accepted | 2026-11-14 |
| [0002](0002-flask-monolith-with-json-api.md) | Монолітний Flask-застосунок із вбудованим JSON API | Accepted | 2026-11-14 |
| [0003](0003-documentation-as-code-mkdocs.md) | Documentation as Code: MkDocs Material і strict-збірка | Accepted | 2026-11-17 |
| [0004](0004-api-first-openapi-contract.md) | API-first: контракт OpenAPI як єдине джерело істини | Accepted | 2026-11-17 |

Пов'язані документи: [SDD](../sdd.md), [ISD](../isd.md), [регламент підтримки документації](../../developer/maintenance.md).
