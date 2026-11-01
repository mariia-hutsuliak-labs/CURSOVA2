"""
Лабораторна робота №7: незмінні об'єкти-значення (Value Objects) для продажу.

SaleLine  - одна позиція продажу (товар, кількість, ціна одиниці, знижка).
SaleOrder - усі позиції продажу разом.

Обидва класи frozen: після створення поля змінити неможливо. Знижка рахується
на льоту у властивості total_price і НІКОЛИ не перезаписує базову ціну товару.
"""
from dataclasses import dataclass
from decimal import Decimal

from models import Product, SaleItem


@dataclass(frozen=True)
class SaleLine:
    product_id: int
    quantity: int
    unit_price: Decimal
    discount_rate: float = 0.0

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Кількість у позиції продажу має бути додатною")
        if not 0.0 <= self.discount_rate < 1.0:
            raise ValueError("Знижка має бути в діапазоні [0, 1)")

    @property
    def total_price(self) -> float:
        return float(self.unit_price) * self.quantity * (1 - self.discount_rate)

    def write_off_stock(self) -> None:
        Product.query.get(self.product_id).stock_quantity -= self.quantity

    def to_item(self, sale_id: int) -> SaleItem:
        return SaleItem(
            sale_id=sale_id,
            product_id=self.product_id,
            quantity=self.quantity,
            unit_price=self.unit_price,
            total_price=self.total_price,
        )


@dataclass(frozen=True)
class SaleOrder:
    lines: tuple

    @classmethod
    def from_items(cls, items: dict, discount_rate: float = 0.0) -> "SaleOrder":
        """items: {product_id: quantity}. Ціни беруться з каталогу лише для читання."""
        return cls(tuple(
            SaleLine(product_id, quantity, Product.query.get(product_id).price, discount_rate)
            for product_id, quantity in items.items()
        ))

    @property
    def total(self) -> float:
        return sum(line.total_price for line in self.lines)

    def write_off_stock(self) -> None:
        for line in self.lines:
            line.write_off_stock()

    def to_items(self, sale_id: int) -> tuple:
        return tuple(line.to_item(sale_id) for line in self.lines)