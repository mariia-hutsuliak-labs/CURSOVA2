from sqlalchemy import func

from analytics.contracts import PeriodResolver
from models import Contract, Delivery, DeliveryItem, Supplier


class ProcurementQueries:
    """Закупівлі: договори за період і вартість поставок постачальника: query_3, query_9."""

    def __init__(self, session, periods: PeriodResolver):
        self._session = session
        self._periods = periods

    def query_3_contracts_by_period(self, period_type='month'):
        start_date, end_date = self._periods.resolve(period_type)

        query = self._session.query(Contract).filter(
            Contract.start_date.between(start_date, end_date)
        )

        return query.all()

    def query_9_supplier_product_value(self, supplier_name, target_date=None):
        if not target_date:
            target_date = self._periods.today()

        query = self._session.query(
            func.sum(DeliveryItem.total_price).label('total_value')
        ).join(Delivery).join(Contract).join(Supplier).filter(
            Supplier.name == supplier_name,
            Delivery.delivery_date <= target_date
        )

        result = query.first()
        return result.total_value if result.total_value else 0
