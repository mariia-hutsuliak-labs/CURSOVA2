#!/usr/bin/env python3
"""
ЛР8, Завдання 3: краш-тест вертикальних зв'язків ієрархії ціноутворення (pricing/).

Для кожного з трьох калькуляторів викликає контрактні методи
(line_total, describe_line, apply_discount) і друкує OK + значення або ПОМИЛКУ.
Запуск з кореня проєкту:
    python3 scripts/lab8_inheritance_test.py
Код завершення: 0 = усе працює, 1 = є збої.
"""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricing import build_calculators   # noqa: E402

SCENARIOS = [
    ("line_total(100, 3, 0.1)", lambda c: c.line_total(100, 3, Decimal("0.1"))),
    ("line_total(250.5, 12)", lambda c: c.line_total(250.5, 12)),
    ("describe_line(80, 2, 0.05)", lambda c: c.describe_line(80, 2, Decimal("0.05"))),
    ("apply_discount(100, 0.1)", lambda c: c.apply_discount(Decimal("100"), Decimal("0.1"))),
]


def run(call, calculator):
    try:
        return True, call(calculator)
    except Exception as exc:   # noqa: BLE001 (краш-тест має зловити будь-яку помилку)
        return False, "%s: %s" % (type(exc).__name__, str(exc)[:80])


def main():
    broken = total = 0
    for name, calculator in build_calculators().items():
        for label, call in SCENARIOS:
            ok, value = run(call, calculator)
            total += 1
            broken += 0 if ok else 1
            print("%-8s %-28s %s  %s" % (name, label, "OK    " if ok else "ПОМИЛКА", value))
    print("\nЗламано: %d з %d" % (broken, total))
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
