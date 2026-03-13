from django.contrib import admin
from .models import DailySalesReport, MonthlySalesReport


@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'branch', 'product', 'total_sold', 'total_revenue')
    list_filter = ('branch', 'product', 'date')
    readonly_fields = ('branch', 'product', 'date', 'total_sold', 'total_revenue', 'last_updated')
    date_hierarchy = 'date'


@admin.register(MonthlySalesReport)
class MonthlySalesReportAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'branch', 'product', 'total_sold', 'total_revenue')
    list_filter = ('branch', 'product', 'year', 'month')
    readonly_fields = ('branch', 'product', 'year', 'month', 'total_sold', 'total_revenue', 'last_updated')