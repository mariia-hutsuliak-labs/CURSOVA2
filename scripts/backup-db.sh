#!/usr/bin/env bash
# Щодобова резервна копія (ISD §8.4): дамп БД + архів history/, шифрування, ротація.
# Запуск вручну або з cron:  0 2 * * *  cd /Users/mac/projects/CURSOVA2 && bash scripts/backup-db.sh
# Для шифрування потрібна змінна BACKUP_PASSPHRASE у .env (необов'язково: без неї копії не шифруються).
set -euo pipefail
set -a; . ./.env; set +a
PG_URL="${DATABASE_URL/+psycopg2/}"
DAY="$(date -u +%Y-%m-%d)"
mkdir -p backups

pg_dump -Fc "$PG_URL" -f "backups/bookstore_${DAY}.dump"
tar -czf "backups/history_${DAY}.tar.gz" history/
pg_restore --list "backups/bookstore_${DAY}.dump" > /dev/null   # дамп читається

if [ -n "${BACKUP_PASSPHRASE:-}" ]; then
  for f in "backups/bookstore_${DAY}.dump" "backups/history_${DAY}.tar.gz"; do
    openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -in "$f" -out "$f.enc"
  done
  echo "Зашифровано: backups/*_${DAY}.*.enc (відкриті копії лишаються лише локально, див. ISD §8.4)"
fi

# Ротація локальних копій: 7 щоденних (старші за 7 днів видаляються)
find backups -maxdepth 1 -name 'bookstore_*.dump*' -mtime +7 -delete
find backups -maxdepth 1 -name 'history_*.tar.gz*' -mtime +7 -delete
echo "Резервну копію ${DAY} створено."
