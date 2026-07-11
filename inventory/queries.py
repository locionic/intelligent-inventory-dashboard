from django.db import connection
from django.db.models import F, Value, IntegerField, Case, When, BooleanField, ExpressionWrapper, DurationField
from django.db.models.functions import ExtractDay
from django.db.models.expressions import RawSQL
from django.utils import timezone
import datetime

def get_annotated_vehicles():
    """
    Returns a queryset of vehicles annotated with days_in_stock and is_aging.
    All calculations are done at the database level.
    """
    from inventory.models import Vehicle
    today = timezone.localdate()
    
    # Calculate days_in_stock at database level, supporting both SQLite and other databases.
    if connection.vendor == 'sqlite':
        days_in_stock_expr = RawSQL(
            "CAST(julianday(%s) - julianday(intake_date) AS INTEGER)",
            [str(today)]
        )
    else:
        days_in_stock_expr = ExtractDay(
            ExpressionWrapper(Value(today) - F('intake_date'), output_field=DurationField())
        )
        
    # Calculate is_aging: status is 'in_stock' and intake_date is more than 90 days ago (strictly > 90)
    is_aging_expr = Case(
        When(
            status=Vehicle.Status.IN_STOCK,
            intake_date__lt=today - datetime.timedelta(days=90),
            then=Value(True)


        ),
        default=Value(False),
        output_field=BooleanField()
    )
    
    return Vehicle.objects.annotate(
        days_in_stock=days_in_stock_expr,
        is_aging=is_aging_expr
    )
