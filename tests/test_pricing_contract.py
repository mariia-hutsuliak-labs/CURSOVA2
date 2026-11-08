"""Контрактні (регресійні) тести шару pricing/ (ЛР8, Завдання 3).

Фіксують поведінку трьох калькуляторів через публічний контракт:
вони мають проходити і в стані Baseline (успадкування), і після рефакторингу
(композиція), а в стані FAIL падають: саме так регресія стає видимою.
"""
from decimal import Decimal

import pytest

from pricing import build_calculators


@pytest.fixture
def calcs():
    return build_calculators()


@pytest.mark.parametrize("name, expected", [
    ("base", ("324.00", "3607.20")),
    ("retail", ("324.00", "3607.20")),
    ("loyalty", ("266.40", "2830.40")),
])
def test_line_total(calcs, name, expected):
    calc = calcs[name]
    assert calc.line_total(100, 3, Decimal("0.1")) == Decimal(expected[0])
    assert calc.line_total(250.5, 12) == Decimal(expected[1])


@pytest.mark.parametrize("name, expected", [
    ("base", "2 x 80 грн = 182.40 грн"),
    ("retail", "2 шт. по 80.00 грн (знижка 5%) = 182.40 грн"),
    ("loyalty", "[gold] 2 шт. по 80.00 грн (членам клубу) (знижка 5%) = 150.70 грн (членам клубу)"),
])
def test_describe_line(calcs, name, expected):
    assert calcs[name].describe_line(80, 2, Decimal("0.05")) == expected


@pytest.mark.parametrize("name, expected", [("base", "90.0"), ("retail", "90.0"), ("loyalty", "83.00")])
def test_apply_discount(calcs, name, expected):
    assert calcs[name].apply_discount(Decimal("100"), Decimal("0.1")) == Decimal(expected)


def test_retail_order_total_with_and_without_shipping(calcs):
    retail = calcs["retail"]
    assert retail.order_total([(100, 3, Decimal("0.1")), (250.5, 12, 0)]) == Decimal("3931.20")
    assert retail.order_total([(10, 1, 0)]) == Decimal("72.00")


def test_loyalty_specific_rules(calcs):
    loyalty = calcs["loyalty"]
    assert loyalty.order_total([(10, 1, 0)]) == Decimal("70.00")
    assert loyalty.points_earned(Decimal("266.40")) == 26
    assert (loyalty.level_name(), loyalty.member_rate()) == ("gold", Decimal("0.07"))
    assert loyalty.line_total(10, 60, 0) == Decimal("532.90")      # автоматична оптова знижка
    assert loyalty.line_total(1, 1, Decimal("0.99")) == Decimal("1.10")   # мінімальна ціна


def test_price_floor_and_history(calcs):
    retail = calcs["retail"]
    assert retail.line_total(1, 1, Decimal("0.99")) == Decimal("1.20")
    assert retail.history()[-1] == ("line_total", Decimal("1.20"))


@pytest.mark.parametrize("name, quantity", [("base", 0), ("retail", 1001), ("loyalty", 1001)])
def test_invalid_quantity_is_rejected(calcs, name, quantity):
    with pytest.raises(ValueError):
        calcs[name].line_total(1, quantity)
