---
owner: Mariia Hutsuliak
status: published
review_date: 2027-02-12
tags: [architecture, ops]
---

# ISD: специфікація інфраструктури (Infrastructure Specification Document)

Цей документ відповідає на питання «де і на чому система працює, як її розгорнути і відновити». Внутрішню структуру описано в [sdd.md](sdd.md).

Власник: Mariia Hutsuliak. Цикл перегляду: 90 днів (експлуатаційна документація), див. [maintenance.md](../developer/maintenance.md).

Позначки статусу: **[є]** реалізовано в репозиторії, **[ціль]** цільове значення, ще не реалізоване.

## 1. Топологія розгортання

Поточна топологія: **локальна**. Один процес Flask (`python app.py`, `debug=True`, порт 5000) і окремий сервер PostgreSQL на тій самій машині (`localhost:5432`). Контейнеризація застосовується лише для ізольованого раннера вимірювання метрик якості (`Dockerfile.quality`, `docker-compose.quality.yml`), а не для самого застосунку.

| Компонент SDD | Де запускається | Порядок підняття |
|---|---|---|
| PostgreSQL | локальний сервер або окремий контейнер | 1 (до застосунку) |
| `init_db.py` | одноразово, створює таблиці й початкових користувачів | 2 |
| Flask Web App (`app.py`, `models.py`, `analytics/`, `sale_values.py`, `inventory_alerts.py`, `resilience.py`, `privacy/*`, `templates/`) | `python app.py`. Перший крок старту: `validate_config()` перевіряє `LOW_STOCK_THRESHOLD` ще до підключення до БД; при помилці процес завершується | 3 |
| Історія запитів (`history_utils.py`) | каталог `history/` у корені проєкту, створюється застосунком | разом із застосунком |
| Журнал (`privacy/secure_logging.py`) | stderr, за потреби файл `LOG_FILE` | разом із застосунком |

## 2. Середовища

| Середовище | Призначення | Конфігурація | Статус |
|---|---|---|---|
| dev | розробка на ноутбуці | `.env` із `.env.example`, `debug=True` | [є] |
| test | автотести `pytest` | ті самі `app.py` і БД, що в dev; фікстура `client` логіниться як `operator` через реальний `/login`, тому потрібна БД, ініціалізована `init_db.py` | [є] |
| quality-runner | відтворюване вимірювання метрик (ЛР5); охоплює `app.py`, `models.py`, `analytics/`, `privacy/`, `resilience.py`, `history_utils.py` | Docker, Python 3.11.13, ліміти 1 CPU і 1 ГБ RAM | [є] |
| production | промислова експлуатація | WSGI-сервер (наприклад gunicorn) за reverse proxy, `debug=False`, окрема БД, секрети зі сховища секретів | [ціль] |

## 3. Змінні середовища (без значень секретів)

| Змінна | Обов'язкова | За замовчуванням | Призначення | Де читається |
|---|---|---|---|---|
| `SECRET_KEY` | так | немає | ключ підпису сесій Flask | `app.py` |
| `DATABASE_URL` | так | немає | рядок підключення SQLAlchemy до PostgreSQL | `app.py` |
| `POOL_RECYCLE` | ні | `300` | час (с) переробки з'єднань пулу | `app.py` |
| `LOW_STOCK_THRESHOLD` | ні | `5` | поріг низького залишку товару; має бути цілим числом >= 0, інакше застосунок не стартує (fail-fast) | `inventory_alerts.py` (перевірка при імпорті `app.py`) |
| `DEMO_API_TOKEN` | ні | порожньо | токен демо-скрипта виявлення секретів (ЛР3) | `secrets_trap_demo.py` |
| `DB_FAULT_MODE` | ні | `none` | імітація збою БД: `none`, `error`, `timeout` (ЛР2) | `fault_injection.py` |
| `LOG_FORMAT` | ні | `text` | формат логів: `text` або `json` | `privacy/secure_logging.py` |
| `LOG_FILE` | ні | немає | додатковий файл журналу | `privacy/secure_logging.py` |

Реальні значення зберігаються лише в локальному `.env` (він у `.gitignore`); зразок без секретів: `.env.example`.

## 4. Сховища даних

| Сховище | Що містить | Технологія | Резервне копіювання |
|---|---|---|---|
| PostgreSQL | бізнес-таблиці, користувачі, згоди, аудит приватності (див. [sdd.md §4](sdd.md)) | PostgreSQL, SQLAlchemy 1.4, psycopg2-binary | [ціль] щодобовий `pg_dump` |
| `history/user_<id>.json` | історія аналітичних запитів користувача | JSON-файли з блокуванням `threading.Lock` | [ціль] копіювання разом із дампом БД |

## 5. CI/CD і контроль якості

**[є]** Конвеєр `.github/workflows/complexity.yml` («Complexity and Hotspots»).
Тригери: `push` і `pull_request`. Образ: `python:3.11`. Стадії: checkout з повною історією (`fetch-depth: 0`) → Radon 6.0.1 цикломатична складність у JSON → code churn за 90 днів (`git log`) → hotspot-матриця (`scripts/hotspots.py`) → вивантаження артефактів `complexity-reports`.

**[є]** Локальні Quality Gates (`scripts/hooks/pre-commit`, підключається `git config core.hooksPath scripts/hooks`): Gitleaks (блокує коміт із секретом) і Radon (блокує коміт, якщо цикломатична складність функції CC > 10).

**[є]** Статичний аналіз SonarQube (ЛР8): конфігурація `sonar-project.properties` (проєкт CURSOVA2, сервер `http://localhost:9000`, Python 3.9, виключення: tests, reports, history, templates); сервер піднімається локально, у CI не входить.

**[є]** Скрипти аудиту об'єктного дизайну (ЛР8): `scripts/ck_metrics.py` (метрики Chidamber-Kemerer і MOOD), `scripts/coupling_matrix.py` (матриця зв'язності), `scripts/lab8_crash_test.py` та `scripts/lab8_inheritance_test.py` (краш-тести); результати в `reports/lab8/`.

**[є]** Повторювані перевірки: `scripts/sca-audit.sh` (pip-audit, залежності), `scripts/secret-scan.sh` (повна історія на секрети), `scripts/measure-quality.sh` (метрики в Docker), `scripts/doc-audit.sh` (актуальність документації, ЛР10).

**[ціль]** Додати `scripts/doc-audit.sh` як обов'язкову стадію конвеєра, щоб злиття з дрейфом документації блокувалося.

## 6. Моніторинг

**[ціль]** Моніторинг поки не реалізований. Мінімальний набір: перевірка доступності `GET /login` (HTTP 200) кожну хвилину; сповіщення, якщо PostgreSQL недоступний понад 1 хвилину (застосунок уже має retry з backoff: 3 спроби, 0.3 с, множник 2); аналіз журналу на події рівня ERROR.

## 7. Резервне копіювання та відновлення (RTO/RPO)

| Показник | Цільове значення | Пояснення |
|---|---|---|
| RPO (Recovery Point Objective): допустима втрата даних | 24 години | щодобовий дамп; для навчальної книгарні втрата продажів за добу прийнятна, ручне відновлення можливе з паперових чеків |
| RTO (Recovery Time Objective): допустимий час відновлення | 4 години | час на розгортання нового сервера, відновлення дампа і перевірку |

**[ціль]** Відновлення: `createdb bookstore` → `pg_restore` (або `psql < dump.sql`) → `.env` з актуальним `DATABASE_URL` → `python app.py` → перевірка входу та `/api/query10`. Відкат релізу: `git checkout <попередній тег>` і перезапуск процесу; схема БД створюється `db.create_all()` без міграцій, тому зміна схеми потребує ручного узгодження (відомий ризик, див. [ADR-0002](adr/0002-flask-monolith-with-json-api.md)).
