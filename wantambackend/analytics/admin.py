from django.contrib import admin
import calendar
from django.db.models import Sum
from .models import DailySalesReport, MonthlySalesReport


@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'branch', 'product', 'total_sold', 'total_revenue','last_updated')
    list_filter = ('branch', 'product', 'date')
    ordering = ('-date',)
    search_fields = ('branch__name', 'product__name')   
    readonly_fields = ('branch', 'product', 'date', 'total_sold', 'total_revenue', 'last_updated')
    date_hierarchy = 'date'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
 
        totals = qs.aggregate(
            grand_total_sold=Sum('total_sold'),
            grand_total_revenue=Sum('total_revenue'),
        )
        response.context_data['grand_total_sold'] = totals['grand_total_sold'] or 0
        response.context_data['grand_total_revenue'] = totals['grand_total_revenue'] or 0
        return response


@admin.register(MonthlySalesReport)
class MonthlySalesReportAdmin(admin.ModelAdmin):
    list_display = ('year', 'get_month_name', 'branch', 'product', 'total_sold', 'total_revenue','last_updated')
    list_filter = ('branch', 'product', 'year', 'month')
    ordering = ('-year', '-month')
    search_fields = ('branch__name', 'product__name')   
    readonly_fields = ('branch', 'product', 'year', 'month', 'total_sold', 'total_revenue', 'last_updated')
    
    @admin.display(description='Month', ordering='month')
    def get_month_name(self, obj):
        """Display month as name e.g. 'March' instead of 3."""
        return calendar.month_name[obj.month]
 
    # --- ADDED: Show grand totals at the bottom of the changelist ---
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
 
        totals = qs.aggregate(
            grand_total_sold=Sum('total_sold'),
            grand_total_revenue=Sum('total_revenue'),
        )
        response.context_data['grand_total_sold'] = totals['grand_total_sold'] or 0
        response.context_data['grand_total_revenue'] = totals['grand_total_revenue'] or 0
        return response