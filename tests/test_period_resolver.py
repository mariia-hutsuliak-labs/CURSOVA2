"""Юніт-тести CalendarPeriodResolver (без БД): межі періодів збігаються з логікою,
яка раніше дублювалась у query_3, query_5 і query_10."""
from datetime import date

import pytest

from analytics.period import CalendarPeriodResolver

R = CalendarPeriodResolver()


@pytest.mark.parametrize("period, anchor, expected", [
    ("day", date(2026, 11, 8), (date(2026, 11, 8), date(2026, 11, 8))),
    ("week", date(2026, 11, 8), (date(2026, 11, 2), date(2026, 11, 8))),      # неділя -> тиждень з понеділка
    ("week", date(2026, 11, 2), (date(2026, 11, 2), date(2026, 11, 8))),      # понеділок
    ("month", date(2026, 2, 10), (date(2026, 2, 1), date(2026, 2, 28))),
    ("month", date(2028, 2, 10), (date(2028, 2, 1), date(2028, 2, 29))),      # високосний рік
    ("month", date(2026, 12, 15), (date(2026, 12, 1), date(2026, 12, 31))),   # грудень
    ("quarter", date(2026, 5, 20), (date(2026, 4, 1), date(2026, 6, 30))),
    ("quarter", date(2026, 11, 8), (date(2026, 10, 1), date(2026, 12, 31))),
    ("year", date(2026, 7, 4), (date(2026, 1, 1), date(2026, 12, 31))),
])
def test_resolve_boundaries(period, anchor, expected):
    assert R.resolve(period, anchor) == expected


def test_trailing_is_inclusive_window():
    assert R.trailing(7, date(2026, 11, 8)) == (date(2026, 11, 1), date(2026, 11, 8))


def test_defaults_use_today():
    assert R.resolve("day") == (date.today(), date.today())
    assert R.trailing(7)[1] == date.today()


def test_unknown_period_is_rejected():
    with pytest.raises(ValueError):
        R.resolve("decade")
    with pytest.raises(ValueError):
        R.resolve(None)
