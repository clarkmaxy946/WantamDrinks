# analytics/urls.py
from django.urls import path
from .views import (
    DailySalesReportView,
    MonthlySalesReportView,
    BranchDailySummaryView,
    BranchMonthlySummaryView,
    ProductSalesView,
)

urlpatterns = [
    # Static paths before dynamic paths
    path('admin/analytics/daily/', DailySalesReportView.as_view(), name='analytics-daily'),
    path('admin/analytics/daily/summary/', BranchDailySummaryView.as_view(), name='analytics-daily-summary'),
    path('admin/analytics/monthly/', MonthlySalesReportView.as_view(), name='analytics-monthly'),
    path('admin/analytics/monthly/summary/', BranchMonthlySummaryView.as_view(), name='analytics-monthly-summary'),
    path('admin/analytics/products/<str:product_name>/', ProductSalesView.as_view(), name='analytics-product'),
]