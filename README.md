# CURSOVA2: інформаційна система книгарні

Вебзастосунок для обліку роботи книжкового магазину: товари (книги), продажі, поставки від постачальників, договори, працівники та графіки змін, аналітичні звіти. Розроблений як курсовий проєкт, далі використовується як об'єкт лабораторних з «Інженерії якості та СПС».

**Для кого:** адміністратор і оператор книгарні (облік і звіти), авторизований користувач (перегляд і звіти), гість (обмежений перегляд).

**Що вміє система:**

- облік товарів, категорій, працівників, відділів, постачальників, договорів;
- оформлення продажів і поставок із автоматичним перерахунком залишків;
- контроль залишків: оператор бачить товари, яких лишилося мало (`/api/inventory/low-stock`, поріг задається змінною `LOW_STOCK_THRESHOLD`, за замовчуванням 5);
- 10 аналітичних запитів (`/api/query1` ... `/api/query10`) та довільний SQL-запит для оператора;
- рольовий доступ: `guest`, `authorized_user`, `operator`, `administrator`; реєстрація нових користувачів через заявку, яку схвалює адміністратор;
- права суб'єкта даних (privacy): експорт персональних даних, анонімізація, керування згодами.

## Швидкий старт (для новачка)

Потрібно: Python 3.9 (версія середовища проєкту, див. `docs/architecture/isd.md`), PostgreSQL, Git.

```bash
git clone https://github.com/mariia-hutsuliak-labs/CURSOVA2.git
cd CURSOVA2
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # відкрийте .env і заповніть SECRET_KEY та DATABASE_URL
                                     # LOW_STOCK_THRESHOLD має бути цілим числом, інакше застосунок не запуститься
createdb bookstore                   # або створіть БД будь-яким іншим способом у PostgreSQL

python init_db.py                    # створює таблиці й тестові дані (admin / operator)
python app.py                        # запуск на http://127.0.0.1:5000
```

Увійдіть як `admin` (пароль із `init_db.py`, лише для локальної розробки; у production змініть).

Перевірка, що все працює:

```bash
python -m pytest tests/              # автотести
bash scripts/doc-audit.sh            # аудит актуальності документації
```

## Карта документації

| Хочу зрозуміти... | Документ |
|---|---|
| як система влаштована всередині (компоненти, модель даних, API) | [docs/architecture/sdd.md](docs/architecture/sdd.md) |
| де і як вона розгортається, середовища, CI/CD, відновлення | [docs/architecture/isd.md](docs/architecture/isd.md) |
| чому прийняті саме такі рішення | [docs/architecture/adr/](docs/architecture/adr/0001-postgresql-as-primary-store.md) |
| хто відповідає за документи і як часто їх переглядають | [docs/developer/maintenance.md](docs/developer/maintenance.md) |
| яка політика безпеки залежностей і секретів | [SECURITY.md](SECURITY.md) |
| як вносити зміни й що перевіряється перед злиттям | [docs/developer/CONTRIBUTING.md](docs/developer/CONTRIBUTING.md) |
| історичний аудит ЛР10 (застаріла сторінка) | [docs/developer/audit.md](docs/developer/audit.md) |

## Правило внесків

**Зміна коду = зміна документації.** Якщо ви додаєте маршрут, змінну середовища чи компонент, оновіть `docs/architecture/sdd.md` та/або `docs/architecture/isd.md` у тому самому коміті. Перед злиттям запускайте `bash scripts/doc-audit.sh`: код завершення 1 означає, що документація відстала.

## Definition of Done для документації

Зміна вважається завершеною, коли пройдено всі перевірки нижче. Детальний чек-лист `docs-or-don't-merge` наведено в [правилах внесків](docs/developer/CONTRIBUTING.md).

| Вимір | Що перевіряється | Інструмент | Де виконується |
|---|---|---|---|
| Контракти | OpenAPI валідний, є описи й приклади | Spectral (`.spectral.yaml`) | локально перед PR |
| Розмітка | єдиний стиль Markdown | markdownlint-cli2 | CI, крок Lint |
| Посилання і збірка | немає битих посилань і навігації, сайт збирається | `mkdocs build --strict` | CI, крок Strict build |
| Актуальність | є паспорт, `review_date` не прострочений | `scripts/check_review_dates.py` | CI, крок Review date audit |
| Дрейф коду й документів | немає маршрутів і змінних без опису | `scripts/doc-audit.sh` | локально перед PR |
| Режими відмови | для компонентів зі станом описано відмови й є тести на них | `pytest`, чек-лист надійності в PR | локально перед PR |
