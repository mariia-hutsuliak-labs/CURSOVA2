"""Штучна трирівнева ієрархія ціноутворення для ЛР8 (Завдання 3, Baseline).

У проєкті немає ланцюга успадкування глибиною >= 3, тому, за приміткою методички,
створено демонстраційну ієрархію сервісів:

    BasePriceCalculator            (DIT = 1)  базові правила
      RetailPriceCalculator        (DIT = 2)  роздріб: переписує половину логіки батька
        LoyaltyPriceCalculator     (DIT = 3)  клуб лояльності: переписує ще більше

Нащадки перевизначають методи батьків і спираються на їхні внутрішні виклики
(self.discount_amount, super().apply_discount ...), тому зміна в батьку
каскадно ламає нижні рівні.
"""
from decimal import Decimal, ROUND_HALF_UP


class BasePriceCalculator:
    """Рівень 1: базові правила ціноутворення."""

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


class RetailPriceCalculator(BasePriceCalculator):
    """Рівень 2: роздріб. Перевизначає 5 методів батька, частину логіки переписує заново."""

    MIN_PRICE = Decimal("1.00")
    MAX_QUANTITY = 1000

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
        # логіку батька переписано заново (а не super): додано мінімальну ціну
        discounted = price - self.discount_amount(price, rate)
        return max(discounted, self.MIN_PRICE)

    def round_price(self, price):
        step = Decimal("0.05")
        return (price / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step

    def validate_quantity(self, quantity):
        super().validate_quantity(quantity)
        if quantity > self.MAX_QUANTITY:
            raise ValueError("Забагато одиниць в одному рядку")
        return quantity

    def format_price(self, price):
        return "{:,.2f} грн".format(price).replace(",", " ")

    def describe_line(self, base_price, quantity, rate=0):
        total = self.line_total(base_price, quantity, rate)
        return "%d шт. по %s (знижка %s) = %s" % (
            quantity, self.format_price(self.net_price(base_price)),
            self.discount_percent_text(rate), self.format_price(total))


class LoyaltyPriceCalculator(RetailPriceCalculator):
    """Рівень 3: клуб лояльності. Перевизначає 6 методів, line_total переписано повністю."""

    BOOKS_VAT_RATE = Decimal("0.07")
    LEVEL_RATES = {"silver": Decimal("0.03"), "gold": Decimal("0.07")}

    def __init__(self, level="silver"):
        super().__init__()
        self._level = level

    def member_rate(self):
        return self.LEVEL_RATES.get(self._level, Decimal("0"))

    def points_earned(self, total):
        return int(total // 10)

    def expiry_note(self):
        return "Бали діють 12 місяців"

    def level_name(self):
        return self._level

    def apply_discount(self, price, rate):
        # знову переписано: знижка клієнта додається до загальної
        discount = self.discount_amount(price, Decimal(str(rate)) + self.member_rate())
        return max(price - discount, self.MIN_PRICE)

    def vat_amount(self, price):
        return price * self.BOOKS_VAT_RATE

    def line_total(self, base_price, quantity, rate=0):
        # повністю переписаний метод батька: додається автоматична оптова знижка
        self.validate_quantity(quantity)
        auto_rate = self.bulk_discount_rate(quantity)
        discounted = self.apply_discount(self.net_price(base_price), Decimal(str(rate)) + auto_rate)
        total = self.round_price(self.gross_price(discounted) * quantity)
        self._log.append(("line_total", total))
        return total

    def round_price(self, price):
        step = Decimal("0.10")
        return (price / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step

    def format_price(self, price):
        return "%s (членам клубу)" % super().format_price(price)

    def describe_line(self, base_price, quantity, rate=0):
        return "[%s] %s" % (self._level, super().describe_line(base_price, quantity, rate))
