"""Аналітичний шар: замість одного класу-мутанта BookstoreQueries (God Object).

Composition root: єдине місце, де інтерфейси зв'язуються з реалізаціями.
Решта коду отримує готові об'єкти і не знає про конкретні класи.
"""
from types import SimpleNamespace

from analytics.employee_queries import EmployeeQueries
from analytics.lookup_queries import LookupQueries
from analytics.period import CalendarPeriodResolver
from analytics.procurement_queries import ProcurementQueries
from analytics.revenue_queries import RevenueQueries


def build_analytics(session, periods=None):
    periods = periods or CalendarPeriodResolver()
    return SimpleNamespace(
        employees=EmployeeQueries(session, periods),
        revenue=RevenueQueries(session, periods),
        lookup=LookupQueries(session),
        procurement=ProcurementQueries(session, periods),
    )
