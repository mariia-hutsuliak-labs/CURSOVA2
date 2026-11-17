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
git clone https://github.com/MariiaHutsuliak/CURSOVA2.git
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
| який стан документації зараз | [docs/developer/audit.md](docs/developer/audit.md) |

## Правило внесків

**Зміна коду = зміна документації.** Якщо ви додаєте маршрут, змінну середовища чи компонент, оновіть `docs/architecture/sdd.md` та/або `docs/architecture/isd.md` у тому самому коміті. Перед злиттям запускайте `bash scripts/doc-audit.sh`: код завершення 1 означає, що документація відстала.
