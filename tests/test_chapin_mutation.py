"""
Лабораторна робота №7, Завдання 2: краш-тест неконтрольованої мутації даних
у replace_sale_items (app.py).

Сценарій: оптовий продаж (10 шт.) зі знижкою 10%. Очікується, що знижка діє лише
на цей продаж, а базова ціна товару в каталозі НЕ змінюється.
"""
import uuid
from decimal import Decimal

import pytest

from app import app as flask_app, replace_sale_items
from models import db, Department, ProductCategory, Employee, Product, Sale, SaleItem


@pytest.fixture
def env():
    tag = uuid.uuid4().hex[:8]
    with flask_app.app_context():
        dept = Department(name=f"L7-{tag}")
        category = ProductCategory(name=f"L7-CAT-{tag}")
        db.session.add_all([dept, category])
        db.session.flush()
        employee = Employee(first_name="Тест", last_name=f"L7-{tag}", position="Продавець",
                            department_id=dept.id)
        product = Product(name=f"L7-Книга-{tag}", price=Decimal("100.00"), stock_quantity=50,
                          category_id=category.id, department_id=dept.id)
        db.session.add_all([employee, product])
        db.session.flush()
        sale = Sale(employee_id=employee.id, total_amount=Decimal("0.00"))
        db.session.add(sale)
        db.session.commit()
        ids = {"sale": sale.id, "product": product.id, "employee": employee.id,
               "dept": dept.id, "category": category.id}

    yield ids

    with flask_app.app_context():
        db.session.rollback()
        SaleItem.query.filter_by(sale_id=ids["sale"]).delete()
        Sale.query.filter_by(id=ids["sale"]).delete()
        Product.query.filter_by(id=ids["product"]).delete()
        Employee.query.filter_by(id=ids["employee"]).delete()
        ProductCategory.query.filter_by(id=ids["category"]).delete()
        Department.query.filter_by(id=ids["dept"]).delete()
        db.session.commit()


def test_discount_must_not_overwrite_base_price(env):
    with flask_app.app_context():
        sale = db.session.get(Sale, env["sale"])
        total = replace_sale_items(sale, {env["product"]: 10}, discount_rate=0.10)
        db.session.commit()
        db.session.expire_all()

        assert total == pytest.approx(900.0), "оптова сума зі знижкою 10% має бути 900"
        base_price = Decimal(db.session.get(Product, env["product"]).price)
        assert base_price == Decimal("100.00"), (
            f"КАСОВИЙ РОЗРИВ: базова ціна в каталозі стала {base_price} замість 100.00"
        )