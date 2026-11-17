#!/usr/bin/env bash
# ЛР10: повторюваний аудит актуальності документації (Documentation Decay Audit).
# Запуск з кореня проєкту:  bash scripts/doc-audit.sh
# Код завершення 0 = документація актуальна, 1 = виявлено дрейф (Documentation Decay).
#
# Метрики (пороги з ЛР10):
#   1. Last Updated Age      — днів від останнього коміту документа (>90 підозрілий, >180 застарілий)
#   2. Code-Doc Change Ratio — скільки комітів коду було ПІСЛЯ останнього оновлення документа (>20 = структурний дрейф)
#   3. Structure Drift       — API-маршрути з app.py, яких немає в docs/architecture/sdd.md
#   4. Config Drift          — змінні середовища з коду, яких немає в docs/architecture/isd.md
set -uo pipefail
cd "$(dirname "$0")/.."

TODAY=$(date +%s)
FAIL=0
DOCS="README.md docs/architecture/sdd.md docs/architecture/isd.md docs/developer/maintenance.md docs/architecture/adr/0001-postgresql-as-primary-store.md docs/architecture/adr/0002-flask-monolith-with-json-api.md"
CODE_PATHS="app.py models.py analytics pricing sale_values.py history_utils.py resilience.py fault_injection.py privacy"

echo "== 1-2. Last Updated Age та Code-Doc Change Ratio =="
printf "%-62s %-11s %-6s %s\n" "Документ" "Оновлено" "Днів" "Комітів коду після"
for f in $DOCS; do
  [ -f "$f" ] || { printf "%-62s %s\n" "$f" "ВІДСУТНІЙ"; FAIL=1; continue; }
  h=$(git log -1 --format=%H -- "$f")
  if [ -z "$h" ]; then printf "%-62s %s\n" "$f" "не закомічено"; continue; fi
  ct=$(git log -1 --format=%ct -- "$f")
  age=$(( (TODAY - ct) / 86400 ))
  drift=$(git log --oneline "$h"..HEAD -- $CODE_PATHS | wc -l | tr -d ' ')
  mark=""
  [ "$age" -gt 90 ] && mark="$mark [AGE>90]"
  [ "$drift" -gt 20 ] && { mark="$mark [DRIFT>20]"; FAIL=1; }
  printf "%-62s %-11s %-6s %s%s\n" "$f" "$(git log -1 --format=%cs -- "$f")" "$age" "$drift" "$mark"
done

echo
echo "== 3. Structure Drift: API-маршрути в коді, яких немає в docs/architecture/sdd.md =="
MISSING_ROUTES=0
for r in $(grep -oE "@app\.route\('/api/[^']+'" app.py | sed "s/@app.route('//; s/'$//" | sort -u); do
  if ! grep -qF "$r" docs/architecture/sdd.md 2>/dev/null; then echo "  НЕ ЗАДОКУМЕНТОВАНО: $r"; MISSING_ROUTES=$((MISSING_ROUTES+1)); fi
done
TOTAL_ROUTES=$(grep -oE "@app\.route\('/api/[^']+'" app.py | sort -u | wc -l | tr -d ' ')
echo "  Маршрутів /api/* у коді: $TOTAL_ROUTES, без опису в SDD: $MISSING_ROUTES"
[ "$MISSING_ROUTES" -gt 0 ] && FAIL=1

echo
echo "== 4. Config Drift: змінні середовища в коді, яких немає в docs/architecture/isd.md =="
MISSING_ENV=0
# Лише файли під контролем Git (без .venv, site-packages та інших сторонніх каталогів), без tests/
ENVS=$(git ls-files '*.py' | grep -v '^tests/' | xargs grep -hoE "os\.getenv\(\"?'?[A-Z_]+" 2>/dev/null | sed -E "s/os\.getenv\(\"?'?//" | grep -v '_ENV$' | sort -u)
ENVS="$ENVS DB_FAULT_MODE"
for v in $(echo $ENVS | tr ' ' '\n' | sort -u); do
  if ! grep -qF "$v" docs/architecture/isd.md 2>/dev/null; then echo "  НЕ ЗАДОКУМЕНТОВАНО: $v"; MISSING_ENV=$((MISSING_ENV+1)); fi
done
echo "  Змінних без опису в ISD: $MISSING_ENV"
[ "$MISSING_ENV" -gt 0 ] && FAIL=1

echo
echo "== 5. Component Drift: модулі, які імпортує app.py, але яких немає в docs/architecture/sdd.md =="
MISSING_MODS=0
for m in $(grep -E "^from [a-z_]+(\.[a-z_]+)* import" app.py | awk '{print $2}' | cut -d. -f1 | sort -u); do
  if [ -f "$m.py" ] || [ -d "$m" ]; then
    if ! grep -qF "$m" docs/architecture/sdd.md 2>/dev/null; then echo "  НЕ ЗАДОКУМЕНТОВАНО: $m"; MISSING_MODS=$((MISSING_MODS+1)); fi
  fi
done
echo "  Модулів без опису в SDD: $MISSING_MODS"
[ "$MISSING_MODS" -gt 0 ] && FAIL=1

if [ "$FAIL" -eq 0 ]; then echo "ВЕРДИКТ: PASS — документація відповідає коду"; else echo "ВЕРДИКТ: FAIL — виявлено Documentation Decay"; fi
exit $FAIL
