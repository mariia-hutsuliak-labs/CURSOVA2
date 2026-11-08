from sqlalchemy import func

from analytics.contracts import PeriodResolver
from models import Product, ProductCategory, Sale, SaleItem


class RevenueQueries:
    """Виручка від продажів: query_2, query_10."""

    def __init__(self, session, periods: PeriodResolver):
        self._session = session
        self._periods = periods

    def query_2_revenue_analysis(self, start_date=None, end_date=None, category_name=None):
        if not start_date:
            start_date, end_date = self._periods.resolve('month')

        query = self._session.query(
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(Sale).join(Product)

        if category_name:
            query = query.join(ProductCategory).filter(ProductCategory.name == category_name)

        query = query.filter(Sale.sold_on >= start_date, Sale.sold_on <= end_date)

        result = query.first()
        return result.total_revenue if result.total_revenue else 0

    def query_10_weekly_sales_analysis(self, from_date=None):
        start_date, end_date = self._periods.trailing(7, from_date)

        total_query = (
            self._session.query(func.sum(SaleItem.total_price).label('total_sales'))
            .select_from(SaleItem)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(Sale.sold_on >= start_date, Sale.sold_on <= end_date)
        )

        total_result = total_query.first()
        total_sales = total_result.total_sales if total_result.total_sales else 0

        category_query = (
            self._session.query(
                ProductCategory.name,
                func.sum(SaleItem.total_price).label('category_sales')
            )
            .select_from(ProductCategory)
            .join(Product, Product.category_id == ProductCategory.id)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(Sale.sold_on >= start_date, Sale.sold_on <= end_date)
            .group_by(ProductCategory.id, ProductCategory.name)
        )

        category_results = category_query.all()

        return {
            'total_sales': total_sales,
            'by_category': category_results,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
