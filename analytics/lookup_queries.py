from sqlalchemy import extract

from models import Contract, ContractProduct, Product, ProductCategory, Sale, SaleItem, Supplier


class LookupQueries:
    """Вибірки без агрегації за періодом: query_4, query_6, query_8."""

    def __init__(self, session):
        self._session = session

    def query_4_suppliers_without_board_games(self):
        board_games_category = self._session.query(ProductCategory).filter(
            ProductCategory.name.like('%настільн%')
        ).first()

        if not board_games_category:
            return self._session.query(Supplier).all()

        suppliers_with_board_games = self._session.query(Supplier.id).join(Contract).join(
            ContractProduct
        ).join(Product).filter(
            Product.category_id == board_games_category.id
        ).subquery()

        query = self._session.query(Supplier).filter(
            ~Supplier.id.in_(suppliers_with_board_games)
        )

        return query.all()

    def query_6_sales_info(self, target_date=None, month=None, category_name=None, supplier_name=None):
        query = (
            self._session.query(Sale, SaleItem, Product, ProductCategory)
            .join(SaleItem, SaleItem.sale_id == Sale.id)
            .join(Product, Product.id == SaleItem.product_id)
            .join(ProductCategory, ProductCategory.id == Product.category_id)
        )

        if target_date:
            query = query.filter(Sale.sold_on == target_date)

        if month:
            query = query.filter(extract('month', Sale.sold_on) == month)

        if category_name:
            query = query.filter(ProductCategory.name == category_name)

        if supplier_name:
            query = (
                query.join(ContractProduct, ContractProduct.product_id == Product.id)
                .join(Contract, Contract.id == ContractProduct.contract_id)
                .join(Supplier, Supplier.id == Contract.supplier_id)
                .filter(Supplier.name == supplier_name)
            )

        return query.all()

    def query_8_supplier_by_contract(self, contract_number):
        result = self._session.query(Supplier, Contract).join(Contract).filter(
            Contract.contract_number == contract_number
        ).first()

        return result
