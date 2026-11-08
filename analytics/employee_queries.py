from sqlalchemy import func

from analytics.contracts import PeriodResolver
from models import Department, Employee, Sale, WorkSchedule


class EmployeeQueries:
    """Співробітники та їхні продажі: query_1, query_5, query_7."""

    def __init__(self, session, periods: PeriodResolver):
        self._session = session      # Dependency Injection: сесія БД
        self._periods = periods      # Dependency Injection: інтерфейс, а не реалізація

    def query_1_employees_info(self, department_name=None, managers_only=False, on_vacation_only=False):
        query = self._session.query(Employee).join(Department)

        if department_name:
            query = query.filter(Department.name == department_name)

        if managers_only:
            query = query.filter(Employee.position.like('%керівник%'))

        if on_vacation_only:
            query = query.filter(Employee.is_on_vacation == True)

        return query.all()

    def query_5_top_sellers(self, min_amount=200, period_type='day', target_date=None):
        start_date, end_date = self._periods.resolve(period_type, target_date)

        query = self._session.query(
            Employee,
            func.sum(Sale.total_amount).label('total_sales'),
            func.count(Sale.id).label('sales_count')
        ).join(Sale).filter(
            Sale.sold_on >= start_date, Sale.sold_on <= end_date
        ).group_by(Employee.id)

        if min_amount:
            query = query.having(func.sum(Sale.total_amount) > min_amount)

        return query.all()

    def query_7_employee_count(self, target_date=None, department_name=None):
        if not target_date:
            return {'employees': [], 'count': 0}

        query = (
            self._session.query(Employee, WorkSchedule, Department)
            .select_from(WorkSchedule)
            .join(Employee, Employee.id == WorkSchedule.employee_id)
            .join(Department, Department.id == Employee.department_id)
            .filter(WorkSchedule.work_date == target_date)
        )

        if department_name:
            query = query.filter(Department.name == department_name)

        employees = query.all()

        return {
            'employees': employees,
            'count': len(employees)
        }
