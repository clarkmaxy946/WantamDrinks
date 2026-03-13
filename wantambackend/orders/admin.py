# orders/admin.py
from django.contrib import admin
from django import forms
from .models import Order, OrderItem
from products.models import Product


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tell Django this field is not required from the form side
        # Our clean_ method always fills it from the product
        self.fields['price_at_purchase'].required = False
        self.fields['price_at_purchase'].widget.attrs['readonly'] = True
        self.fields['price_at_purchase'].help_text = "Auto-filled from selected product on save"

        # Pre-fill when editing an existing item
        if self.instance and self.instance.pk:
            self.fields['price_at_purchase'].initial = self.instance.product.price

    def clean_price_at_purchase(self):
        product = self.cleaned_data.get('product')
        if product:
            return product.price
        raise forms.ValidationError("Select a product first.")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemForm
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'branch', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'branch']
    search_fields = ['order_id', 'user__email', 'transaction_id']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    form = OrderItemForm
    list_display = ['order', 'product', 'quantity', 'price_at_purchase']
