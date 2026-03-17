# analytics/serializers.py
import calendar
from rest_framework import serializers
from .models import DailySalesReport, MonthlySalesReport


class DailySalesReportSerializer(serializers.ModelSerializer):
    """
    Used in:
    - GET /api/admin/analytics/daily/
    - GET /api/admin/analytics/daily/?branch=BRN-NBI
    - GET /api/admin/analytics/daily/?date=2026-03-17
    - GET /api/admin/analytics/daily/?product=Coke
    """

    # String representations instead of nested objects
    # Flat design keeps response fast for thousands of records
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )
    total_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        coerce_to_string=False  # Return as number for frontend calculations
    )

    class Meta:
        model = DailySalesReport
        fields = [
            'branch_name',      # "Nairobi" instead of BRN-NBI
            'product_name',     # "Coke" instead of PRD-001
            'date',             # 2026-03-17
            'total_sold',       # Units sold that day
            'total_revenue',    # KES earned that day
            'last_updated',     # How fresh is this data
        ]
        read_only_fields = fields


class MonthlySalesReportSerializer(serializers.ModelSerializer):
    """
    Used in:
    - GET /api/admin/analytics/monthly/
    - GET /api/admin/analytics/monthly/?branch=BRN-NBI
    - GET /api/admin/analytics/monthly/?year=2026
    - GET /api/admin/analytics/monthly/?month=3
    """

    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )
    total_revenue = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
        coerce_to_string=False
    )

    # Human readable month — "March" instead of 3
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySalesReport
        fields = [
            'branch_name',
            'product_name',
            'year',             # 2026
            'month',            # 3
            'month_name',       # "March"
            'total_sold',       # Units sold that month
            'total_revenue',    # KES earned that month
            'last_updated',
        ]
        read_only_fields = fields

    def get_month_name(self, obj):
        
        return calendar.month_name[obj.month]


class BranchDailySummarySerializer(serializers.Serializer):
    """
   Used in:
    - GET /api/admin/analytics/daily/summary/
    - GET /api/admin/analytics/daily/summary/?date=2026-03-17
    """

    branch_name = serializers.CharField()
    date = serializers.DateField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        coerce_to_string=False
    )


class BranchMonthlySummarySerializer(serializers.Serializer):
    """
    Used in:
    - GET /api/admin/analytics/monthly/summary/
    - GET /api/admin/analytics/monthly/summary/?year=2026&month=3
    """

    branch_name = serializers.CharField()
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    month_name = serializers.SerializerMethodField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        coerce_to_string=False
    )

    def get_month_name(self, obj):
        
        return calendar.month_name[obj['month']]


class ProductSalesSerializer(serializers.Serializer):
    """
    Used in:
    - GET /api/admin/analytics/products/<product_name>/
    - GET /api/admin/analytics/products/<product_name>/?month=3&year=2026
    """

    product_name = serializers.CharField()
    branch_name = serializers.CharField()
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    month_name = serializers.SerializerMethodField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        coerce_to_string=False
    )

    def get_month_name(self, obj):
        return calendar.month_name[obj['month']]
