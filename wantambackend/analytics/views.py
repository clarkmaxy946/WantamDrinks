# analytics/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Sum, F
from django.utils import timezone
from .models import DailySalesReport, MonthlySalesReport
from .serializers import (
    DailySalesReportSerializer,
    MonthlySalesReportSerializer,
    BranchDailySummarySerializer,
    BranchMonthlySummarySerializer,
    ProductSalesSerializer,
)


class DailySalesReportView(APIView):
    """
    GET /api/admin/analytics/daily/
    Admin only — requires is_staff=True.
    Daily sales snapshots per product per branch.
    Data pre-computed via update_sales_analytics() — no scanning of orders.

    Filterable by:
    ?date=2026-03-19        → specific day
    ?branch_id=NRB001       → specific branch
    ?product_id=PRD-001     → specific product
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        reports = DailySalesReport.objects.select_related(
            'branch',
            'product'
        ).order_by('-date')

        # Filter by date
        date = request.query_params.get('date')
        if date:
            reports = reports.filter(date=date)

        # Filter by branch
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            reports = reports.filter(branch__branch_id=branch_id)

        # Filter by product
        product_id = request.query_params.get('product_id')
        if product_id:
            reports = reports.filter(product__product_id=product_id)

        serializer = DailySalesReportSerializer(reports, many=True)
        data = serializer.data
        return Response(
            {
                "total_records": len(data),
                "reports": data
            },
            status=status.HTTP_200_OK
        )


class MonthlySalesReportView(APIView):
    """
    GET /api/admin/analytics/monthly/
    Admin only — requires is_staff=True.
    Monthly sales trends per product per branch.
    Month returned as name e.g. "March" not 3.

    Filterable by:
    ?year=2026          → specific year
    ?month=3            → specific month
    ?branch_id=NRB001   → specific branch
    ?product_id=PRD-001 → specific product
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        reports = MonthlySalesReport.objects.select_related(
            'branch',
            'product'
        ).order_by('-year', '-month')

        # Filter by year
        year = request.query_params.get('year')
        if year:
            reports = reports.filter(year=year)

        # Filter by month
        month = request.query_params.get('month')
        if month:
            reports = reports.filter(month=month)

        # Filter by branch
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            reports = reports.filter(branch__branch_id=branch_id)

        # Filter by product
        product_id = request.query_params.get('product_id')
        if product_id:
            reports = reports.filter(product__product_id=product_id)

        serializer = MonthlySalesReportSerializer(reports, many=True)
        data = serializer.data
        return Response(
            {
                "total_records": len(data),
                "reports": data
            },
            status=status.HTTP_200_OK
        )


class BranchDailySummaryView(APIView):
    """
    GET /api/admin/analytics/daily/summary/
    Admin only — requires is_staff=True.
    Aggregates ALL products into one total per branch per day.
    DB-level aggregation via Sum() — never in Python.

    Instead of:
        Nairobi | Coke   | 45 sold | KES 2700
        Nairobi | Fanta  | 30 sold | KES 1800
        Nairobi | Sprite | 25 sold | KES 1500

    Returns:
        Nairobi | 100 sold | KES 6000

    Filterable by:
    ?date=2026-03-19    → specific day (defaults to today)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Default to today if no date provided
        date = request.query_params.get('date', timezone.now().date())

        # Aggregate at DB level — Sum() is faster than Python loops
        summaries = DailySalesReport.objects.filter(
            date=date
        ).values(
            'branch__name'
        ).annotate(
            branch_name=F('branch__name'),
            total_sold=Sum('total_sold'),
            total_revenue=Sum('total_revenue')
        ).order_by('branch__name')

        # Add date to each record for serializer
        data = [
            {
                'branch_name': s['branch_name'],
                'date': date,
                'total_sold': s['total_sold'],
                'total_revenue': s['total_revenue'],
            }
            for s in summaries
        ]

        serializer = BranchDailySummarySerializer(data, many=True)
        return Response(
            {
                "date": str(date),
                "total_branches": len(data),
                "summary": serializer.data
            },
            status=status.HTTP_200_OK
        )


class BranchMonthlySummaryView(APIView):
    """
    GET /api/admin/analytics/monthly/summary/
    Admin only — requires is_staff=True.
    Aggregates ALL products into one total per branch per month.
    DB-level aggregation via Sum().

    Filterable by:
    ?year=2026   → specific year (defaults to current year)
    ?month=3     → specific month (defaults to current month)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        now = timezone.now()

        # Default to current year and month
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))

        summaries = MonthlySalesReport.objects.filter(
            year=year,
            month=month
        ).values(
            'branch__name'
        ).annotate(
            branch_name=F('branch__name'),
            total_sold=Sum('total_sold'),
            total_revenue=Sum('total_revenue')
        ).order_by('branch__name')

        data = [
            {
                'branch_name': s['branch_name'],
                'year': year,
                'month': month,
                'total_sold': s['total_sold'],
                'total_revenue': s['total_revenue'],
            }
            for s in summaries
        ]

        serializer = BranchMonthlySummarySerializer(data, many=True)
        return Response(
            {
                "year": year,
                "month": month,
                "total_branches": len(data),
                "summary": serializer.data
            },
            status=status.HTTP_200_OK
        )


class ProductSalesView(APIView):
    """
    GET /api/admin/analytics/products/<product_name>/
    Admin only — requires is_staff=True.
    Shows performance of one product across ALL branches.

    e.g. How is Coke selling in every branch this month?

    Filterable by:
    ?year=2026   → specific year (defaults to current year)
    ?month=3     → specific month (defaults to current month)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, product_name):
        now = timezone.now()
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))

        reports = MonthlySalesReport.objects.filter(
            product__name__iexact=product_name,
            year=year,
            month=month
        ).select_related(
            'branch',
            'product'
        ).order_by('branch__name')

        if not reports.exists():
            return Response(
                {
                    "error": f"No sales data found for '{product_name}' "
                             f"in {year}-{str(month).zfill(2)}."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = [
            {
                'product_name': r.product.name,
                'branch_name': r.branch.name,
                'year': r.year,
                'month': r.month,
                'total_sold': r.total_sold,
                'total_revenue': r.total_revenue,
            }
            for r in reports
        ]

        serializer = ProductSalesSerializer(data, many=True)
        return Response(
            {
                "product": product_name,
                "year": year,
                "month": month,
                "total_branches": len(data),
                "reports": serializer.data
            },
            status=status.HTTP_200_OK
        )