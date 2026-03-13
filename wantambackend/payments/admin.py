# payments/admin.py
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_id',
        'order',
        'user',
        'phone_number',
        'amount',
        'status',
        'receipt_number',
        'created_at'
    )
    list_filter = ('status',)
    search_fields = (
        'payment_id',
        'order__order_id',
        'receipt_number',
        'checkout_request_id',
        'user__email'
    )
    readonly_fields = (
        'payment_id',
        'order',
        'user',
        'phone_number',
        'amount',
        'checkout_request_id',
        'merchant_request_id',
        'receipt_number',
        'failure_reason',
        'raw_callback',
        'created_at',
        'updated_at'
    )
    date_hierarchy = 'created_at'
