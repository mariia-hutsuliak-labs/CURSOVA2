"""
ЛР10, краш-тест Documentation Decay: новий компонент контролю залишків.

Повертає товари, залишок яких не перевищує поріг. Поріг береться зі змінної
середовища LOW_STOCK_THRESHOLD (за замовчуванням 5). Некоректне значення
зупиняє запуск застосунку (fail-fast) через validate_config().
"""
import os

from models import Product

DEFAULT_LOW_STOCK_THRESHOLD = 5


def validate_config():
    """Перевіряє LOW_STOCK_THRESHOLD під час старту; кидає ValueError, якщо це не невід'ємне ціле."""
    raw = os.getenv("LOW_STOCK_THRESHOLD", str(DEFAULT_LOW_STOCK_THRESHOLD))
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"LOW_STOCK_THRESHOLD має бути цілим числом, отримано: {raw!r}")
    if value < 0:
        raise ValueError("LOW_STOCK_THRESHOLD не може бути від'ємним")
    return value


def find_low_stock_products(threshold=None):
    """Не видалені товари із залишком <= threshold, від найменшого залишку."""
    if threshold is None:
        threshold = validate_config()
    return (
        Product.query
        .filter(Product.is_deleted == False, Product.stock_quantity <= threshold)  # noqa: E712
        .order_by(Product.stock_quantity.asc(), Product.name.asc())
        .all()
    )
