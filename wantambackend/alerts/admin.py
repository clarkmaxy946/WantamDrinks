# alerts/admin.py
from django.contrib import admin
from .models import StockAlert


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('branch', 'product', 'severity', 'stock_at_alert', 'threshold', 'is_resolved', 'created_at')
    list_filter = ('severity', 'is_resolved', 'branch', 'product')
    readonly_fields = ('inventory', 'branch', 'product', 'severity', 'stock_at_alert', 'threshold', 'created_at', 'resolved_at', 'resolved_by')