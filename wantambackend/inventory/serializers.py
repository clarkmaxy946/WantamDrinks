# inventory/serializers.py
from rest_framework import serializers
from .models import Inventory, RestockLog
from branches.serializers import BranchSerializer
from products.serializers import ProductSerializer


class InventorySerializer(serializers.ModelSerializer):

    branch = BranchSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'branch',
            'product',
            'stock',
            'is_in_stock',
            'low_stock_threshold',
        ]
        read_only_fields = fields

    def get_is_in_stock(self, obj):
        return obj.is_in_stock


class RestockLogSerializer(serializers.ModelSerializer):

    restocked_by = serializers.StringRelatedField(read_only=True)
    branch_name  = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = RestockLog
        fields = [
            'branch_name',
            'product_name',
            'restocked_by',
            'quantity_added',
            'stock_before',
            'stock_after',
            'restocked_at',
        ]
        read_only_fields = fields

    def get_branch_name(self, obj):
        return obj.inventory.branch.name if obj.inventory and obj.inventory.branch else '—'

    def get_product_name(self, obj):
        return obj.inventory.product.name if obj.inventory and obj.inventory.product else '—'


class AdminInventorySerializer(serializers.ModelSerializer):

    branch = BranchSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    is_low = serializers.SerializerMethodField()
    restock_history = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'branch',
            'product',
            'stock',
            'is_in_stock',
            'is_low',
            'low_stock_threshold',
            'last_updated',
            'restock_history',
        ]
        read_only_fields = [
            'branch',
            'product',
            'stock',
            'is_in_stock',
            'is_low',
            'last_updated',
            'restock_history',
        ]

    def get_is_in_stock(self, obj):
        return obj.is_in_stock

    def get_is_low(self, obj):
        return obj.is_low

    def get_restock_history(self, obj):
        logs = obj.restock_logs.all().order_by('-restocked_at')[:10]
        return RestockLogSerializer(logs, many=True).data

    def validate_low_stock_threshold(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Low stock threshold must be at least 1. "
                "A value of 0 would cause alerts to never fire."
            )
        return value


class RestockSerializer(serializers.Serializer):

    quantity = serializers.IntegerField(
        min_value=1,
        help_text="Number of units to add to current stock"
    )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Restock quantity must be a positive number."
            )
        return value