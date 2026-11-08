#!/usr/bin/env python3
"""
ЛР8, Завдання 2: краш-тест запитів аналітичного шару (analytics/).
У стані FAIL (до декомпозиції) ті самі 10 запитів викликались зі старого класу BookstoreQueries.

Викликає всі 10 аналітичних запитів у контексті Flask-застосунку (реальна БД з .env)
і друкує для кожного OK або ПОМИЛКУ. Запускати з кореня проєкту:
    python3 scripts/lab8_crash_test.py
Код завершення: 0 = усі 10 запитів працюють, 1 = є зламані.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, analytics_services as svc   # noqa: E402  (реальна проводка застосунку і БД)

# (назва, функція виклику): аргументи за замовчуванням, щоб кожен запит відпрацював
CASES = [
    ("query_1_employees_info", lambda: svc.employees.query_1_employees_info()),
    ("query_2_revenue_analysis", lambda: svc.revenue.query_2_revenue_analysis()),
    ("query_3_contracts_by_period", lambda: svc.procurement.query_3_contracts_by_period("month")),
    ("query_4_suppliers_without_board_games", lambda: svc.lookup.query_4_suppliers_without_board_games()),
    ("query_5_top_sellers", lambda: svc.employees.query_5_top_sellers()),
    ("query_6_sales_info", lambda: svc.lookup.query_6_sales_info(target_date=date.today())),
    ("query_7_employee_count", lambda: svc.employees.query_7_employee_count()),
    ("query_8_supplier_by_contract", lambda: svc.lookup.query_8_supplier_by_contract("0")),
    ("query_9_supplier_product_value", lambda: svc.procurement.query_9_supplier_product_value("x")),
    ("query_10_weekly_sales_analysis", lambda: svc.revenue.query_10_weekly_sales_analysis()),
]


def run_case(name, call):
    """Повертає (успіх, текст помилки)."""
    try:
        result = call()
        if hasattr(result, "all"):       # ледачий Query: виконуємо, щоб дійти до БД
            result.all()
        return True, ""
    except Exception as exc:             # noqa: BLE001 (краш-тест має зловити будь-яку)
        return False, "%s: %s" % (type(exc).__name__, str(exc).splitlines()[0][:110])


def main():
    failed = 0
    with app.app_context():
        for name, call in CASES:
            ok, err = run_case(name, call)
            failed += 0 if ok else 1
            print("%-40s %s" % (name, "OK" if ok else "ПОМИЛКА  " + err))
            if not ok:
                from models import db
                db.session.rollback()    # після збою БД сесія має бути чистою
    print("\nЗламано: %d з %d" % (failed, len(CASES)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
