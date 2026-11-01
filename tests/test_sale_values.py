"""
Лабораторна робота №7: тести Value Objects SaleLine / SaleOrder (без бази даних).
Доводять імутабельність і правила, перенесені всередину об'єктів-значень.
"""
import dataclasses
from decimal import Decimal

import pytest

from sale_values import SaleLine, SaleOrder


def make_line(**overrides):
    fields = {"product_id": 1, "quantity": 10, "unit_price": Decimal("100.00"), "discount_rate": 0.0}
    return SaleLine(**{**fields, **overrides})


def test_line_is_immutable():
    line = make_line()
    with pytest.raises(dataclasses.FrozenInstanceError):
        line.unit_price = Decimal("1.00")


def test_discount_does_not_change_unit_price():
    line = make_line(discount_rate=0.10)
    assert line.total_price == pytest.approx(900.0)
    assert line.unit_price == Decimal("100.00")


def test_default_total_is_price_times_quantity():
    assert make_line().total_price == pytest.approx(1000.0)


@pytest.mark.parametrize("bad", [{"quantity": 0}, {"quantity": -3}, {"discount_rate": -0.1}, {"discount_rate": 1.0}])
def test_invalid_values_are_rejected_inside_the_object(bad):
    with pytest.raises(ValueError):
        make_line(**bad)


def test_order_total_is_sum_of_lines_and_order_is_immutable():
    order = SaleOrder((make_line(), make_line(product_id=2, quantity=1, unit_price=Decimal("50.00"))))
    assert order.total == pytest.approx(1050.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        order.lines = ()