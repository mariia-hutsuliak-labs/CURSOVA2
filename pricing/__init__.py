"""Демонстраційний шар ціноутворення (ЛР8, Завдання 3)."""
from pricing.calculators import (BasePriceCalculator, LoyaltyPriceCalculator,
                                 RetailPriceCalculator)


def build_calculators():
    """Єдине місце створення калькуляторів (composition root для демо)."""
    base = BasePriceCalculator()
    retail = RetailPriceCalculator(base)             # залежності передаються через конструктор
    loyalty = LoyaltyPriceCalculator(retail, "gold")
    return {"base": base, "retail": retail, "loyalty": loyalty}
