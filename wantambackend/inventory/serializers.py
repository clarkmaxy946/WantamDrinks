# inventory/serializers.py
from rest_framework import serializers
from .models import Inventory, RestockLog
from branches.serializers import BranchSerializer
from products.serializers import ProductSerializer


class InventorySerializer(serializers.ModelSerializer):

    branch = BranchSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    # Calls model property — single source of truth
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
        return obj.is_in_stock  # ← model property


class RestockLogSerializer(serializers.ModelSerializer):

    restocked_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RestockLog
        fields = [
            'restocked_by',
            'quantity_added',
            'stock_before',
            'stock_after',
            'restocked_at',
        ]
        read_only_fields = fields


class AdminInventorySerializer(serializers.ModelSerializer):

    branch = BranchSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    is_low = serializers.SerializerMethodField()

    # Changed to SerializerMethodField to avoid
    # "Cannot filter a query once a slice has been taken" error
    # Limit of 10 applied here instead of queryset slice
    restock_history = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'branch',
            'product',
            'stock',
            'is_in_stock',
            'is_low',
            'low_stock_threshold',  # Only editable field via PATCH
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
        return obj.is_in_stock  # ← model property

    def get_is_low(self, obj):
        return obj.is_low  # ← model property

    def get_restock_history(self, obj):
        
        logs = obj.restock_logs.all().order_by('-restocked_at')[:10]
        return RestockLogSerializer(logs, many=True).data


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
