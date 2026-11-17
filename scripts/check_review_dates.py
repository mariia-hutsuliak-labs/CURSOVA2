#!/usr/bin/env python3
"""Безперервний аудит актуальності документації (ЛР11, Завдання 3).

Читає YAML-паспорти (front matter) усіх Markdown-файлів у docs/ і порівнює
поточну дату з полем review_date.

  - Прострочена сторінка (review_date у минулому, статус не deprecated)
    виводиться в переліку; у GitHub Actions додатково створюється попередження.
  - Сторінка без паспорта або з некоректним паспортом - це дефект: код завершення 1.
  - Застарілі сторінки зі статусом deprecated не вважаються простроченими,
    але виводяться окремим списком (їх не видаляють).

Запуск:  python scripts/check_review_dates.py [--today YYYY-MM-DD] [--fail-on-overdue]
Код завершення: 0 - паспорти коректні; 1 - є дефекти паспортів (або прострочені з --fail-on-overdue).
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

VALID_STATUSES = {"draft", "in-review", "published", "deprecated"}
REQUIRED = ("owner", "status", "review_date")


def read_front_matter(path: Path) -> dict:
    """Повертає словник полів паспорта або порожній словник, якщо паспорта немає."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip("'\"")
    return {}  # закривального --- не знайдено


def classify(fm: dict, today: date):
    """Повертає (категорія, деталь): ok | overdue | deprecated | defect."""
    missing = [k for k in REQUIRED if not fm.get(k)]
    if missing:
        return "defect", "немає полів паспорта: " + ", ".join(missing)
    if fm["status"] not in VALID_STATUSES:
        return "defect", f"невідомий status: {fm['status']}"
    try:
        review = date.fromisoformat(fm["review_date"])
    except ValueError:
        return "defect", f"некоректний review_date: {fm['review_date']}"
    if fm["status"] == "deprecated":
        return "deprecated", 0
    if review < today:
        return "overdue", (today - review).days
    return "ok", 0


def collect(docs_dir: str, today: date) -> dict:
    """Групує всі сторінки docs/ за категоріями."""
    groups = {"ok": [], "overdue": [], "deprecated": [], "defect": []}
    for path in sorted(Path(docs_dir).rglob("*.md")):
        fm = read_front_matter(path)
        kind, detail = classify(fm, today)
        groups[kind].append((path, fm, detail))
    return groups


def annotate(level: str, path: Path, title: str, message: str) -> None:
    """Створює анотацію GitHub Actions (тільки в CI)."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::{level} file={path},title={title}::{message}")


def print_overdue(items: list) -> None:
    print(f"\nПрострочені review_date: {len(items)}")
    for path, fm, days in items:
        print(f"  - {path}  (owner: {fm['owner']}, review_date: {fm['review_date']}, прострочено на {days} дн.)")
        annotate("warning", path, "Прострочений review_date",
                 f"review_date {fm['review_date']} минув {days} дн. тому; власник: {fm['owner']}")


def print_deprecated(items: list) -> None:
    print(f"\nЗастарілі сторінки (status: deprecated): {len(items)}")
    for path, fm, _ in items:
        print(f"  - {path}  (замінено на: {fm.get('superseded_by', 'не вказано')})")


def print_defects(items: list) -> None:
    print(f"\nДефекти паспортів: {len(items)}")
    for path, _, reason in items:
        print(f"  - {path}: {reason}")
        annotate("error", path, "Дефект паспорта документа", reason)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--docs", default="docs")
    parser.add_argument("--today", help="дата для перевірки (YYYY-MM-DD), за замовчуванням сьогодні")
    parser.add_argument("--fail-on-overdue", action="store_true")
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    groups = collect(args.docs, today)

    print(f"Аудит актуальності документації станом на {today.isoformat()}")
    print(f"Сторінок з актуальним паспортом: {len(groups['ok'])}")
    print_overdue(groups["overdue"])
    print_deprecated(groups["deprecated"])
    print_defects(groups["defect"])

    failed = bool(groups["defect"]) or (args.fail_on_overdue and bool(groups["overdue"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
