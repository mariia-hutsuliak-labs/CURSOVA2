#!/usr/bin/env python3
"""
Лабораторна робота №7, Завдання 3: синергетична матриця критичних зон (Hotspots).

Поєднує два джерела:
  1) статична складність файлів із JSON-звіту Radon (radon cc -j -s);
  2) динаміка розробки (Code Churn) з історії Git: кількість комітів на файл.

Використання:
  python scripts/hotspots.py <radon-cc.json> <churn.txt> <вихідний.csv>
Markdown-таблиця друкується у stdout, CSV зберігається у вказаний файл.
"""
import csv
import json
import re
import sys

CC_FUNC_LIMIT = 10    # будь-яка функція складніша за 10 робить файл "складним" (критерій методички)
CC_FILE_LIMIT = 100   # або сумарна CC усіх функцій файлу >= 100 (файл-"комбайн")
CHURN_LIMIT = 5       # >= 5 комітів за 90 днів = висока мінливість

CATEGORIES = {
    (True, True): "Hotspot (High Risk)",
    (True, False): "Sleeping Danger",
    (False, True): "Active Development",
    (False, False): "Stable Code",
}
ORDER = list(CATEGORIES.values())


def load_complexity(path):
    with open(path, encoding="utf-8") as handle:
        report = json.load(handle)
    result = {}
    for name, blocks in report.items():
        if isinstance(blocks, list) and blocks:
            complexities = [block["complexity"] for block in blocks]
            result[name.removeprefix("./")] = (sum(complexities), max(complexities), len(blocks))
    return result


def load_churn(path):
    churn = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", line)
            if match:
                churn[match.group(2)] = int(match.group(1))
    return churn


def build_rows(complexity, churn):
    rows = []
    for name, (total, worst, count) in complexity.items():
        commits = churn.get(name, 0)
        is_complex = worst > CC_FUNC_LIMIT or total >= CC_FILE_LIMIT
        is_churny = commits >= CHURN_LIMIT
        rows.append((name, total, worst, count, commits, CATEGORIES[(is_complex, is_churny)]))
    rows.sort(key=lambda row: (ORDER.index(row[5]), -row[4], -row[1]))
    return rows


def main(radon_path, churn_path, csv_path):
    rows = build_rows(load_complexity(radon_path), load_churn(churn_path))
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "total_cc", "max_cc", "functions", "commits_90d", "category"])
        writer.writerows(rows)
    print("| Файл | Сумарна CC | Макс. CC функції | Функцій | Комітів (90 днів) | Категорія ризику |")
    print("|---|---|---|---|---|---|")
    for name, total, worst, count, commits, category in rows:
        print(f"| {name} | {total} | {worst} | {count} | {commits} | {category} |")
    print()
    print(f"Пороги: складний файл = макс. CC > {CC_FUNC_LIMIT} або сумарна CC >= {CC_FILE_LIMIT}; "
          f"мінливий файл = >= {CHURN_LIMIT} комітів за 90 днів.")


if __name__ == "__main__":
    main(*sys.argv[1:4])