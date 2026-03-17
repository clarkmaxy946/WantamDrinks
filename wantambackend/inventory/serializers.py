# inventory/serializers.py
from rest_framework import serializers
from .models import Inventory, RestockLog
from branches.serializers import BranchSerializer
from products.serializers import ProductSerializer


class InventorySerializer(serializers.ModelSerializer):
    """
    Customer-facing inventory serializer.
    Shows stock levels for a specific branch with full
    branch and product context.

    Adds is_in_stock flag to prevent customers from
    attempting to buy unavailable items before reaching M-Pesa.

    Used in:
    - GET /api/inventory/<branch_id>/ → stock levels at a branch
    """

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
    """
    Read-only serializer for restock history.
    Shows the full audit trail of every restock event
    for a specific inventory item.

    Nested inside AdminInventorySerializer.
    Limited to last 10 records at view level.
    """

    # Calls CustomUser.__str__ → "username (WNT-XXXXXX)"
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
    """
    Admin-facing inventory serializer.
    Full operational view with nested restock history.

    Performance notes (enforced at view level):
    - select_related('branch', 'product') — prevents N+1
    - prefetch_related('restock_logs')    — prevents N+1 on logs
    - restock_logs limited to last 10     — prevents huge payloads

    Used in:
    - GET   /api/admin/inventory/              → all inventory records
    - GET   /api/admin/inventory/<branch_id>/  → inventory at one branch
    - PATCH /api/admin/inventory/<branch_id>/<product_id>/ → update threshold
    """

    branch = BranchSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    is_in_stock = serializers.SerializerMethodField()
    is_low = serializers.SerializerMethodField()

    restock_history = RestockLogSerializer(
        source='restock_logs',
        many=True,
        read_only=True
    )

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
        return obj.is_low       # ← model property


class RestockSerializer(serializers.Serializer):
    """
    Admin-only restock input serializer.
    Accepts only the quantity to add — nothing else.

    Connects directly to inventory/services.py → add_stock()
    Does NOT overwrite stock — only increments it.
    Current stock + quantity = new stock.

    Used in:
    - POST /api/admin/inventory/<branch_id>/<product_id>/restock/
    """

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
