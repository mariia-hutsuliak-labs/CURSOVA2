"""Демонстраційний шар ціноутворення (ЛР8, Завдання 3)."""
from pricing.calculators import (BasePriceCalculator, LoyaltyPriceCalculator,
                                 RetailPriceCalculator)


def build_calculators():
    """Єдине місце створення калькуляторів (composition root для демо)."""
    return {
        "base": BasePriceCalculator(),
        "retail": RetailPriceCalculator(),
        "loyalty": LoyaltyPriceCalculator("gold"),
    }
