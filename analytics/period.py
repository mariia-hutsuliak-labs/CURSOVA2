from datetime import date, timedelta
from typing import Optional, Tuple

from dateutil.relativedelta import relativedelta

from analytics.contracts import PeriodResolver


class CalendarPeriodResolver(PeriodResolver):
    """Календарна реалізація PeriodResolver: тиждень починається з понеділка."""

    def today(self) -> date:
        return date.today()

    def resolve(self, period_type: str, anchor: Optional[date] = None) -> Tuple[date, date]:
        calculators = {
            'day': self._day,
            'week': self._week,
            'month': self._month,
            'quarter': self._quarter,
            'year': self._year,
        }
        if period_type not in calculators:
            raise ValueError("Невідомий тип періоду: %r" % (period_type,))
        return calculators[period_type](self._anchor(anchor))

    def trailing(self, days: int, anchor: Optional[date] = None) -> Tuple[date, date]:
        end = self._anchor(anchor)
        return end - timedelta(days=days), end

    def _anchor(self, anchor: Optional[date]) -> date:
        return anchor or self.today()

    def _day(self, anchor: date) -> Tuple[date, date]:
        return anchor, anchor

    def _week(self, anchor: date) -> Tuple[date, date]:
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)

    def _month(self, anchor: date) -> Tuple[date, date]:
        start = date(anchor.year, anchor.month, 1)
        return start, start + relativedelta(months=1) - timedelta(days=1)

    def _quarter(self, anchor: date) -> Tuple[date, date]:
        first_month = (anchor.month - 1) // 3 * 3 + 1
        start = date(anchor.year, first_month, 1)
        return start, start + relativedelta(months=3) - timedelta(days=1)

    def _year(self, anchor: date) -> Tuple[date, date]:
        return date(anchor.year, 1, 1), date(anchor.year, 12, 31)
