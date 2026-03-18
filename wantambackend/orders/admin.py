# orders/admin.py
from django.contrib import admin
from django import forms
from .models import Order, OrderItem


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price_at_purchase'].required = False
        self.fields['price_at_purchase'].widget.attrs['readonly'] = True
        self.fields['price_at_purchase'].help_text = "Auto-filled from selected product on save"

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
    readonly_fields = ['order_id', 'total_price', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

    def save_related(self, request, form, formsets, change):
        """
        Recalculates total_price after all items are saved.
        Fires after inline items are committed to DB.
        """
        super().save_related(request, form, formsets, change)
        order = form.instance
        total = sum(item.subtotal for item in order.items.all())
        Order.objects.filter(pk=order.pk).update(total_price=total)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    form = OrderItemForm
    list_display = ['order', 'product', 'quantity', 'price_at_purchase']
    readonly_fields = ['price_at_purchase']
