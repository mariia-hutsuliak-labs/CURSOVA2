---
owner: Mariia Hutsuliak
status: published
review_date: 2027-05-13
tags: [ops, architecture]
---

# Аудит документації (ЛР10)

Стан на **2026-11-14**, до створення архітектурного паспорта (baseline: HEAD `b3695c7`, 33 коміти, історія з 2026-09-11 до 2026-11-08). Власник: Mariia Hutsuliak. Повторюваний автоматичний аудит: `bash scripts/doc-audit.sh`.

Класифікація: **Продукт** (жива документація, еволюціонує разом із системою) або **Процес** (історичний запис факту в часі). Категорії: **Т** технічна (що система робить), **А** архітектурна (як влаштована), **Е** експлуатаційна (як запускається і супроводжується). Аудиторії: **Dev** розробники, **QA**, **Ops** (DevOps), **Biz** бізнес.

## 1. Інвентаризаційний реєстр

| Документ | Розташування | Тип | Категорія | Аудиторія | Власник | Чого не покриває |
|---|---|---|---|---|---|---|
| Політика безпеки залежностей і секретів | `SECURITY.md` | Продукт | Е | Dev, Ops | M. Hutsuliak | бізнес, QA |
| Зразок конфігурації | `.env.example` | Продукт | Е | Dev, Ops | M. Hutsuliak | бізнес, QA |
| Залежності застосунку | `requirements.txt` | Продукт | Е | Dev, Ops | M. Hutsuliak | бізнес |
| Конвеєр CI | `.github/workflows/complexity.yml` | Продукт | Е | Dev, Ops | M. Hutsuliak | бізнес, QA |
| Раннер метрик | `Dockerfile.quality`, `docker-compose.quality.yml`, `requirements-quality.txt` | Продукт | Е | Ops, QA | M. Hutsuliak | бізнес |
| Скрипти перевірок | `scripts/*.sh`, `scripts/hotspots.py`, `scripts/hooks/pre-commit`, `.gitleaks.toml` | Продукт | Е | Dev, Ops | M. Hutsuliak | бізнес |
| Докстрінги модулів і коментарі в коді | `resilience.py`, `fault_injection.py`, `history_utils.py`, `privacy/*.py`, `sale_values.py`, `analytics/*.py`, `pricing/*.py` | Продукт | Т | Dev | M. Hutsuliak | бізнес, Ops |
| Автотести як контракти поведінки | `tests/*.py` (95 тестів) | Продукт | Т | QA, Dev | M. Hutsuliak | бізнес, Ops |
| Конфігурація SonarQube | `sonar-project.properties` | Продукт | Е | Dev, QA | M. Hutsuliak | Ops, бізнес |
| Скрипти аудиту об'єктного дизайну (ЛР8) | `scripts/ck_metrics.py`, `coupling_matrix.py`, `lab8_crash_test.py`, `lab8_inheritance_test.py` | Продукт | Т | Dev | M. Hutsuliak | бізнес, Ops |
| Звіти SCA | `reports/pip-audit-before.*`, `reports/pip-audit-after.*` | Процес | Е | Dev | M. Hutsuliak | усі, крім розробників |
| Звіти метрик складності | `reports/lizard.xml`, `reports/radon-cc.json`, `reports/radon-mi.json` | Процес | Т | Dev, QA | M. Hutsuliak | бізнес, Ops |
| Звіти ЛР8 (CK/MOOD, зв'язність, SonarQube) | `reports/lab8/*` (15 файлів) | Процес | Т | Dev, QA | M. Hutsuliak | бізнес, Ops |
| Baseline-знімки метрик | `cc_baseline.txt`, `halstead_baseline.txt`, `halstead_total.txt`, `raw_3files.txt` | Процес | Т | Dev | M. Hutsuliak | усі інші |
| Повідомлення комітів | історія Git (33 коміти) | Процес | Т | Dev | M. Hutsuliak | бізнес, Ops |
| Звіти лабораторних ЛР1-9 | `Lab*-Report-Quality.docx` (поза репозиторієм) | Процес | Т/Е | викладач, Dev | M. Hutsuliak | Ops, бізнес |

Відсутні взагалі (прогалини): `README.md`, опис архітектури, опис інфраструктури та відновлення, журнал архітектурних рішень, регламент супроводу. Їх закриває паспорт з Завдання 2.

## 2. Метрики актуальності (baseline)

Команди (з кореня репозиторію):

```bash
git log -1 --format=%cs -- <файл>                      # дата останнього коміту
git log --oneline <хеш_останнього_коміту_файлу>..HEAD -- app.py models.py analytics pricing sale_values.py history_utils.py resilience.py fault_injection.py privacy   # коміти коду після нього
git log --oneline -- app.py | wc -l
git shortlog -sn HEAD
grep -rl --exclude-dir=.git -F "<ім'я файлу>" .        # Access Evidence
```

| Документ | Останнє оновлення | Вік, днів | Коміти коду після оновлення | Згадується в інших файлах (Access Evidence) |
|---|---|---|---|---|
| `SECURITY.md` | 2026-10-01 | 43 | 11 | так, `scripts/sca-audit.sh` |
| `.env.example` | 2026-10-01 | 43 | 11 | ні |
| `requirements.txt` | 2026-10-12 | 32 | 10 | так (CI, Docker) |
| `Dockerfile.quality`, `docker-compose.quality.yml` | 2026-10-18 | 26 | 10 | так (один на одного) |
| `scripts/measure-quality.sh` | 2026-11-08 | 5 | 3 | так (compose) |
| `scripts/sca-audit.sh`, `secret-scan.sh`, `.gitleaks.toml` | 2026-10-01 | 43 | 11 | так (SECURITY.md, hook) |
| `.github/workflows/complexity.yml` | 2026-11-01 | 12 | 5 | так (CI запускається автоматично) |
| `reports/pip-audit-*.{txt,json}` | 2026-10-01 | 43 | 11 | так, `SECURITY.md` |
| `reports/lizard.xml`, `radon-*.json` | 2026-10-18 | 26 | 10 | так, `measure-quality.sh` |
| `sonar-project.properties`, `scripts/ck_metrics.py`, `coupling_matrix.py`, `lab8_*.py`, `reports/lab8/*` | 2026-11-08 | 5 | 2-5 | так: скрипти посилаються на `reports/lab8`; `sonar-project.properties` споживає SonarScanner |
| `cc_baseline.txt`, `halstead_baseline.txt`, `halstead_total.txt`, `raw_3files.txt` | 2026-10-25 | 19 | 10 | **ні, жодного посилання** |

Code-Doc Change Ratio для ключових компонентів за всю історію: `app.py` 14 комітів, `privacy/` 4, `models.py` 4, `pricing/` 3, `analytics/` 1 (пакет з'явився в ЛР8 замість `queries.py`). Жоден документ не перевищив порогів 90 днів і 20 комітів. Найближчі до порога 20: `SECURITY.md` і `.env.example` (11 комітів коду без оновлення). Єдиний автор репозиторію: Mariia Hutsuliak (33 коміти), тобто питань від колег немає, а споживачі документів підтверджені лише посиланнями між файлами.

## 3. Діагноз антипатернів

**Documentation Decay (документ описує систему, якої вже немає):**
1. `SECURITY.md` стверджує, що `Werkzeug` оновлено до 3.1.6, а в `requirements.txt` після коміту 2026-10-12 стоїть 3.1.9; також згадує «13/13 автотестів», тоді як тестів 95. Документ відстав на 11 комітів коду.
2. `.env.example` не містив `LOG_FORMAT`, `LOG_FILE`, `DB_FAULT_MODE`, які код читає з ЛР2 та ЛР4 (Config Drift: 3 змінні з 7).
3. Застарілі згадки колишнього `queries.py` після рефакторингу ЛР8 (його замінив пакет `analytics/`): докстрінг у `seed_bulk_sales.py` («не змінює app.py, models.py, queries.py») і мапа компонентів у `scripts/ck_metrics.py` (`"Infrastructure": "queries.py"`). Файлу вже немає, а коментар і конфігурація на нього вказують.

**Dead Documentation (документ існує, але споживача немає):**
1. `cc_baseline.txt`, `halstead_baseline.txt`, `halstead_total.txt`, `raw_3files.txt`: жоден файл і жоден скрипт на них не посилається, лежать у корені проєкту.

## 4. Матриця вердиктів

| Артефакт | Вердикт | Дія |
|---|---|---|
| `SECURITY.md` | **Оновити** | додано примітку про актуальну версію Werkzeug 3.1.9 і кількість тестів |
| `.env.example` | **Оновити** | додано `LOG_FORMAT`, `LOG_FILE`, `DB_FAULT_MODE` |
| `requirements.txt`, CI, Docker-раннер, скрипти | Залишити | актуальні, мають споживачів |
| `tests/*.py`, докстрінги, `sonar-project.properties`, скрипти й звіти ЛР8 | Залишити | жива документація поведінки / історичний запис |
| Застарілі згадки `queries.py` у `seed_bulk_sales.py` і `scripts/ck_metrics.py` | **Оновити** (за наступного перегляду) | замінити на `analytics/`; це код, тому поза межами ЛР10, зафіксовано як борг |
| `reports/pip-audit-before/after.*`, `reports/lizard.xml`, `radon-*.json` | Залишити як історичний запис | процесні документи, на них посилаються `SECURITY.md` і скрипти |
| `cc_baseline.txt`, `halstead_baseline.txt`, `halstead_total.txt`, `raw_3files.txt` | **Deprecated** | позначено застарілими; перенести в `reports/archive/` або видалити за наступного перегляду (180 днів) після підтвердження, що звіти ЛР6-7 їх не потребують |
| Повідомлення комітів, звіти ЛР1-9 | Залишити | незмінний історичний запис |
| Відсутні README, SDD, ISD, ADR, регламент | **Створити** | паспорт, коміт `docs(architecture): deliver design and infrastructure passport` |

## 5. Матриця покриття аудиторій

| Аудиторія | Ключові питання | Документ-відповідь | Статус baseline | Статус після паспорта |
|---|---|---|---|---|
| Новачок | Як запустити проєкт локально? Які змінні потрібні? Як перевірити, що все працює? | `README.md` (швидкий старт), `.env.example` | прогалина (README немає) | покрито |
| Розробник | З якими компонентами взаємодіє мій модуль? Які є API-маршрути і ролі? Де модель даних? | `docs/sdd.md` | прогалина | покрито |
| QA | Де описані контракти поведінки для перевірок? Як запустити тести? | `docs/sdd.md` §6, `tests/` | частково (тести без опису) | покрито |
| DevOps | Як розгорнути і відкотити реліз? Які середовища, змінні, CI/CD? RTO/RPO? | `docs/isd.md` | прогалина | покрито |
| Бізнес | Що система робить і для кого? | `README.md` (призначення, для кого) | прогалина | покрито |

## Пов'язані документи

- [Регламент підтримки документації](maintenance.md)
- [SDD](../architecture/sdd.md)
- [ISD](../architecture/isd.md)
