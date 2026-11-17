# Журнал змін

Формат: [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/). Версії документації позначаються тегами `docs-vMAJOR.MINOR`.

## [Unreleased]

### Added

- Чек-лист `docs-or-don't-merge` у `docs/developer/CONTRIBUTING.md` і шаблон PR
- Таблиця перевірок Definition of Done для документації в `README.md`
- Автоматичний аудит `review_date` (`scripts/check_review_dates.py`, крок `Review date audit` у конвеєрі)

### Deprecated

- `docs/developer/audit.md` (знімок аудиту ЛР10), замінений `docs/developer/maintenance.md` і автоматичним аудитом

## [docs-v1.0] - 2026-11-17

### Added

- Піраміда документації з чотирьох рівнів, сайт MkDocs Material, паспорти документів, `CODEOWNERS`
- Журнал ADR (0001-0004)
- Контракт OpenAPI 3.0.3 (3 маршрути), Swagger UI з Try it out, перевірка Spectral
- Конвеєр GitHub Actions: markdownlint, `mkdocs build --strict`, деплой на GitHub Pages з `main`
