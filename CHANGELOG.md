# Журнал змін

Формат: [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/). Версії документації позначаються тегами `docs-vMAJOR.MINOR`.

## [Unreleased]

### Added

- Чек-лист `docs-or-don't-merge` у `docs/developer/CONTRIBUTING.md` і шаблон PR
- Таблиця перевірок Definition of Done для документації в `README.md`
- Автоматичний аудит `review_date` (`scripts/check_review_dates.py`, крок `Review date audit` у конвеєрі)
- Експлуатаційний пакет (ЛР12): runbook `docs/runbooks/RB-001.md` (відновлення БД) з каталогом алертів, розділ 8 в `docs/architecture/isd.md` (розгортання, міграції, RTO/RPO, політика резервного копіювання 3-2-1, restore drill), специфікація `docs/slo.yaml` (три SLI, SLO, SLA, Error Budget)
- Скрипти `scripts/backup-db.sh` і `scripts/restore-db.sh`
- Управління змінами (ЛР12): `docs/change-management/` (RFC-001, Impact Analysis, протокол і регламент CCB, Release Checklist)
- Пакет інциденту INC-001 (ЛР12): `docs/incidents/` (Incident Report, Post-Mortem з «5 Чому» і діаграмою Ісікави, план CAPA), `docs/legacy/history-utils.md`, `docs/maintenance-plan.md`, скрипти `scripts/incident_sim.sh` і `scripts/legacy_history_probe.py`
- Тести `tests/test_history_utils.py` (відмови модуля історії запитів)
- Чек-лист надійності (failure-mode) у PR-шаблоні, CONTRIBUTING і Definition of Done (CAPA-3)

### Changed

- `history_utils.py`: атомарний запис файлу історії (тимчасовий файл і `os.replace`), пошкоджений файл переноситься в `user_<id>.json.corrupt-<UTC-час>` замість помилки 500, збій запису історії більше не ламає основний сценарій (CAPA-1, CAPA-2, INC-001)
- `privacy/export.py`: читання історії в режимі `strict`, попередження про карантинні файли
- `privacy/erasure.py`: видалення при анонімізації прибирає й карантинні копії файлу історії

### Deprecated

- `docs/developer/audit.md` (знімок аудиту ЛР10), замінений `docs/developer/maintenance.md` і автоматичним аудитом

## [docs-v1.0] - 2026-11-17

### Added

- Піраміда документації з чотирьох рівнів, сайт MkDocs Material, паспорти документів, `CODEOWNERS`
- Журнал ADR (0001-0004)
- Контракт OpenAPI 3.0.3 (3 маршрути), Swagger UI з Try it out, перевірка Spectral
- Конвеєр GitHub Actions: markdownlint, `mkdocs build --strict`, деплой на GitHub Pages з `main`
