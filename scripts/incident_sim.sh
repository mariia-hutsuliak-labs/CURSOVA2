#!/usr/bin/env bash
# Контрольована симуляція інциденту INC-001 на legacy-компоненті history_utils.py (ЛР12, Завдання 3).
# Імітує збій під час запису: файл history/user_<id>.json обрізається посеред JSON (TD-2 з реєстру боргу).
# Усі події пишуться з часом UTC у reports/incident/INC-001-timeline.log.
#
# Передумова: застосунок запущений (python app.py), працює на http://127.0.0.1:5000.
# Запуск з кореня проєкту:  bash scripts/incident_sim.sh
set -uo pipefail

BASE="${BASE:-http://127.0.0.1:5000}"
OUT="reports/incident"
LOG="$OUT/INC-001-timeline.log"
JAR="$(mktemp)"
mkdir -p "$OUT"
: > "$LOG"

ts()  { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "$(ts) $*" | tee -a "$LOG"; }
code() { curl -s -o /dev/null -m 10 -w "%{http_code}" -b "$JAR" "$BASE$1"; }

log "PREFLIGHT застосунок доступний? GET /login -> $(curl -s -o /dev/null -m 10 -w '%{http_code}' "$BASE/login")"

curl -s -o /dev/null -c "$JAR" -d "username=operator" -d "password=operator123" "$BASE/login"
log "BASELINE login як operator виконано"
B1=$(code /api/query6); B2=$(code /my_history)
log "BASELINE GET /api/query6 -> $B1; GET /my_history -> $B2 (очікується 200 і 200)"
if [ "$B1" != "200" ] || [ "$B2" != "200" ]; then
  log "ABORT базовий стан не зелений, симуляцію не починаю"; exit 1
fi

VICTIM="$(ls -t history/user_*.json | head -1)"
cp "$VICTIM" "$OUT/history_backup_before_incident.json"
log "PREPARE файл історії оператора: $VICTIM (резервна копія в $OUT/history_backup_before_incident.json)"

printf '[{"api": "Запит 6: Деталі продажів", "par' > "$VICTIM"
log "INJECT файл $VICTIM обрізано посеред JSON (імітація збою під час запису, TD-2)"

TOTAL=0; FAILED=0; FIRST_FAIL=""
for i in $(seq 1 10); do
  for path in /api/query6 /my_history; do
    c=$(code "$path"); TOTAL=$((TOTAL+1))
    if [ "$c" != "200" ]; then
      FAILED=$((FAILED+1))
      if [ -z "$FIRST_FAIL" ]; then FIRST_FAIL="$(ts)"; log "DETECT перша помилка: GET $path -> $c (ручне виявлення, алерти ALR-001..003 не налаштовані)"; fi
    fi
  done
  sleep 1
done
log "IMPACT за вікно інциденту: запитів $TOTAL, з помилкою $FAILED (частка помилок $((100*FAILED/TOTAL))%)"

MOVED="$OUT/user_corrupt_$(date -u +%Y%m%dT%H%M%SZ).json"
mv "$VICTIM" "$MOVED"
log "MITIGATE тимчасовий обхід: пошкоджений файл прибрано в $MOVED (історія користувача скидається, звіти працюють)"

A1=$(code /api/query6); A2=$(code /my_history)
log "STABILIZED GET /api/query6 -> $A1; GET /my_history -> $A2"

cp "$OUT/history_backup_before_incident.json" "$VICTIM"
log "CLEANUP файл історії повернуто з резервної копії; симуляцію завершено"
rm -f "$JAR"
