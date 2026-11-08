"""Ціноутворення (ЛР8, Завдання 3, PASS): композиція замість успадкування.

Було:  Loyalty -> Retail -> Base  (extends, DIT = 3, перевизначення методів батьків).
Стало: три незалежні класи (DIT = 1, перевизначень немає); кожен отримує колишнього
батька через конструктор (Dependency Injection), зберігає його як приватне поле
і делегує йому потрібні виклики.

Сигнатуру базового discount_amount(price, rate, currency) знає лише одне місце:
RetailPriceCalculator.discount_amount. Зміна в Base більше не «простріляє» крізь ланцюжок.
"""
from decimal import Decimal, ROUND_HALF_UP


class BasePriceCalculator:
    """Базові правила ціноутворення (не успадковує нікого)."""

    VAT_RATE = Decimal("0.20")
    CURRENCY = "UAH"

    def __init__(self):
        self._log = []

    def net_price(self, base_price):
        return Decimal(str(base_price))

    def discount_amount(self, price, rate, currency):
        """Нова вимога: валюта обов'язкова (зміна сигнатури базового методу)."""
        if currency != self.CURRENCY:
            raise ValueError("Непідтримувана валюта: %s" % currency)
        return price * Decimal(str(rate))

    def apply_discount(self, price, rate):
        return price - self.discount_amount(price, rate, self.CURRENCY)

    def vat_amount(self, price):
        return price * self.VAT_RATE

    def gross_price(self, price):
        return price + self.vat_amount(price)

    def round_price(self, price):
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def validate_quantity(self, quantity):
        if quantity <= 0:
            raise ValueError("Кількість має бути додатною")
        return quantity

    def line_total(self, base_price, quantity, rate=0):
        self.validate_quantity(quantity)
        discounted = self.apply_discount(self.net_price(base_price), rate)
        total = self.round_price(self.gross_price(discounted) * quantity)
        self._log.append(("line_total", total))
        return total

    def format_price(self, price):
        return "%s грн" % price

    def describe_line(self, base_price, quantity, rate=0):
        total = self.line_total(base_price, quantity, rate)
        return "%d x %s = %s" % (quantity, self.format_price(self.net_price(base_price)),
                                 self.format_price(total))

    def unit_price_with_vat(self, base_price):
        return self.round_price(self.gross_price(self.net_price(base_price)))

    def discount_percent_text(self, rate):
        return "%d%%" % (Decimal(str(rate)) * 100)

    def history(self):
        return list(self._log)

    def reset(self):
        self._log = []


class RetailPriceCalculator:
    """Роздріб: має базовий калькулятор як приватне поле (композиція), а не наслідує його."""

    MIN_PRICE = Decimal("1.00")
    MAX_QUANTITY = 1000

    def __init__(self, base):
        self._base = base            # Dependency Injection
        self._log = []

    # --- делегування колишньому батькові ---
    def net_price(self, base_price):
        return self._base.net_price(base_price)

    def discount_amount(self, price, rate):
        # єдине місце в ланцюжку, яке знає поточну сигнатуру base.discount_amount
        return self._base.discount_amount(price, rate, self._base.CURRENCY)

    def gross_price(self, price):
        return self._base.gross_price(price)

    def discount_percent_text(self, rate):
        return self._base.discount_percent_text(rate)

    # --- власна логіка ---
    def bulk_discount_rate(self, quantity):
        if quantity >= 50:
            return Decimal("0.10")
        if quantity >= 10:
            return Decimal("0.05")
        return Decimal("0")

    def shipping_fee(self, total):
        return Decimal("0") if total >= 500 else Decimal("60.00")

    def order_total(self, lines):
        """lines: [(base_price, quantity, rate)]"""
        total = sum((self.line_total(p, q, r) for p, q, r in lines), Decimal("0"))
        return total + self.shipping_fee(total)

    def apply_discount(self, price, rate):
        discounted = price - self.discount_amount(price, rate)
        return max(discounted, self.MIN_PRICE)

    def round_price(self, price):
        step = Decimal("0.05")
        return (price / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step

    def validate_quantity(self, quantity):
        self._base.validate_quantity(quantity)
        if quantity > self.MAX_QUANTITY:
            raise ValueError("Забагато одиниць в одному рядку")
        return quantity

    def line_total(self, base_price, quantity, rate=0):
        self.validate_quantity(quantity)
        discounted = self.apply_discount(self.net_price(base_price), rate)
        total = self.round_price(self.gross_price(discounted) * quantity)
        self._log.append(("line_total", total))
        return total

    def format_price(self, price):
        return "{:,.2f} грн".format(price).replace(",", " ")

    def describe_line(self, base_price, quantity, rate=0):
        total = self.line_total(base_price, quantity, rate)
        return "%d шт. по %s (знижка %s) = %s" % (
            quantity, self.format_price(self.net_price(base_price)),
            self.discount_percent_text(rate), self.format_price(total))

    def history(self):
        return list(self._log)


class LoyaltyPriceCalculator:
    """Клуб лояльності: має роздрібний калькулятор як приватне поле і делегує йому."""

    BOOKS_VAT_RATE = Decimal("0.07")
    LEVEL_RATES = {"silver": Decimal("0.03"), "gold": Decimal("0.07")}

    def __init__(self, retail, level="silver"):
        self._retail = retail        # Dependency Injection
        self._level = level
        self._log = []

    def member_rate(self):
        return self.LEVEL_RATES.get(self._level, Decimal("0"))

    def points_earned(self, total):
        return int(total // 10)

    def expiry_note(self):
        return "Бали діють 12 місяців"

    def level_name(self):
        return self._level

    def apply_discount(self, price, rate):
        discount = self._retail.discount_amount(price, Decimal(str(rate)) + self.member_rate())
        return max(price - discount, self._retail.MIN_PRICE)

    def vat_amount(self, price):
        return price * self.BOOKS_VAT_RATE

    def gross_price(self, price):
        return price + self.vat_amount(price)

    def round_price(self, price):
        step = Decimal("0.10")
        return (price / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step

    def line_total(self, base_price, quantity, rate=0):
        self._retail.validate_quantity(quantity)
        auto_rate = self._retail.bulk_discount_rate(quantity)
        discounted = self.apply_discount(self._retail.net_price(base_price),
                                         Decimal(str(rate)) + auto_rate)
        total = self.round_price(self.gross_price(discounted) * quantity)
        self._log.append(("line_total", total))
        return total

    def order_total(self, lines):
        """lines: [(base_price, quantity, rate)]"""
        total = sum((self.line_total(p, q, r) for p, q, r in lines), Decimal("0"))
        return total + self._retail.shipping_fee(total)

    def format_price(self, price):
        return "%s (членам клубу)" % self._retail.format_price(price)

    def describe_line(self, base_price, quantity, rate=0):
        total = self.line_total(base_price, quantity, rate)
        return "[%s] %d шт. по %s (знижка %s) = %s" % (
            self._level, quantity, self.format_price(self._retail.net_price(base_price)),
            self._retail.discount_percent_text(rate), self.format_price(total))

    def history(self):
        return list(self._log)
