#!/usr/bin/env bash
# Відновлення БД bookstore з дампа (RB-001, рівень автоматизації 1: скриптований).
# Запуск:  bash scripts/restore-db.sh backups/bookstore_YYYY-MM-DD.dump [--target bookstore_drill]
# Без --target відновлює у БД з DATABASE_URL (бойове відновлення).
# З --target відновлює у окрему БД (restore drill), бойові дані не чіпає.
set -euo pipefail

DUMP="${1:?Вкажіть шлях до дампа: bash scripts/restore-db.sh backups/<файл>.dump}"
TARGET=""
if [ "${2:-}" = "--target" ]; then TARGET="${3:?Вкажіть назву БД після --target}"; fi

set -a; . ./.env; set +a
# DATABASE_URL має префікс SQLAlchemy (postgresql+psycopg2://), а psql/pg_restore його не розуміють
PG_URL="${DATABASE_URL/+psycopg2/}"
ADMIN_URL="${PG_URL%/*}/postgres"
DB_NAME="${TARGET:-${PG_URL##*/}}"

[ -f "$DUMP" ] || { echo "ПОМИЛКА: дамп $DUMP не знайдено"; exit 1; }
pg_restore --list "$DUMP" > /dev/null || { echo "ПОМИЛКА: дамп пошкоджено"; exit 1; }

echo "[1/4] Перестворюю БД $DB_NAME"
psql "$ADMIN_URL" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" -c "CREATE DATABASE \"$DB_NAME\";"

echo "[2/4] Відновлюю дані з $DUMP"
pg_restore --no-owner --dbname="${ADMIN_URL%/*}/$DB_NAME" "$DUMP"

echo "[3/4] Перевірка: кількість рядків у ключових таблицях"
psql "${ADMIN_URL%/*}/$DB_NAME" -At -c \
  "SELECT 'users='||count(*) FROM users UNION ALL SELECT 'products='||count(*) FROM products UNION ALL SELECT 'sales='||count(*) FROM sales;"

echo "[4/4] Готово. Далі: запустити застосунок і перевірити GET /login (RB-001, крок 6)."
