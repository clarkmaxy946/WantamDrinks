# inventory/admin.py
from django.contrib import admin
from .models import Inventory, RestockLog


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('branch', 'product', 'stock', 'low_stock_threshold', 'last_updated')
    list_filter = ('branch', 'product')
    readonly_fields = ('last_updated',)


@admin.register(RestockLog)
class RestockLogAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'restocked_by', 'quantity_added', 'stock_before', 'stock_after', 'restocked_at')
    list_filter = ('inventory__branch', 'inventory__product')
    readonly_fields = ('inventory', 'restocked_by', 'quantity_added', 'stock_before', 'stock_after', 'restocked_at')
    date_hierarchy = 'restocked_at'