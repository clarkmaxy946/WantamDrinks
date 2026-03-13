# products/admin.py
from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_id', 'price')
    search_fields = ('name', 'product_id')
    readonly_fields = ('product_id',)