"""Абстрактні контракти (інтерфейси) аналітичного шару.

Прикладні класи залежать від цього інтерфейсу, а не від конкретної реалізації:
календарну логіку можна підмінити (наприклад, у тесті), не чіпаючи SQL-запити.
"""
from abc import ABCMeta, abstractmethod
from datetime import date
from typing import Optional, Tuple


class PeriodResolver(metaclass=ABCMeta):
    """Перетворює тип періоду на межі дат (раніше ця логіка дублювалась у query_3, query_5 і query_10)."""

    @abstractmethod
    def today(self) -> date:
        """Поточна дата (єдине місце, де береться «сьогодні»)."""

    @abstractmethod
    def resolve(self, period_type: str, anchor: Optional[date] = None) -> Tuple[date, date]:
        """day | week | month | quarter | year -> (початок, кінець) включно.
        anchor за замовчуванням сьогодні."""

    @abstractmethod
    def trailing(self, days: int, anchor: Optional[date] = None) -> Tuple[date, date]:
        """Останні `days` днів до anchor включно з ним: (anchor - days, anchor)."""
