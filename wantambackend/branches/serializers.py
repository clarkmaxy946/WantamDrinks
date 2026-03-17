# branches/serializers.py
from rest_framework import serializers
from .models import Branch
from inventory.models import Inventory
from alerts.models import StockAlert
import re


class BranchSerializer(serializers.ModelSerializer):
    """
    Customer-facing branch serializer.
    Read-only — exposes only public fields needed for branch selection.
    Always paired with get_active_branches() in the view to ensure
    only active branches are returned.

    Used in:
    - GET /api/branches/  → customer branch selection screen
    """

    class Meta:
        model = Branch
        fields = [
            'branch_id',    # Used by frontend to fetch branch-specific stock
            'name',         # Nairobi, Mombasa, Thika, Kisumu, Nakuru
            'location',     # Street address or landmark
        ]
        read_only_fields = fields


class AdminBranchSerializer(serializers.ModelSerializer):
    """
    Admin-facing branch serializer.
    Full operational overview including manager details,
    active status, and a live low stock alert summary.
    No choice restriction on name — admin can add any city
    as the business expands.

    Used in:
    - GET   /api/admin/branches/        → full branch list
    - POST  /api/admin/branches/        → create new branch
    - PATCH /api/admin/branches/<id>/   → update branch details
    """

    low_stock_items = serializers.SerializerMethodField()
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'branch_id',
            'name',
            'location',
            'manager_name',
            'manager_phone',
            'is_active',
            'created_at',
            'alert_count',
            'low_stock_items',
        ]
        read_only_fields = [
            'branch_id',
            'created_at',
            'alert_count',
            'low_stock_items',
        ]

    def get_alert_count(self, obj):
        """
        Returns count of unresolved low stock alerts for this branch.
        """
        return StockAlert.objects.filter(
            branch=obj,
            is_resolved=False
        ).count()

    def get_low_stock_items(self, obj):
        """
        Returns full list of products that are low or critical
        at this specific branch.
        """
        alerts = StockAlert.objects.filter(
            branch=obj,
            is_resolved=False
        ).select_related('product', 'inventory')

        if not alerts.exists():
            return []

        items = []
        for alert in alerts:
            items.append({
                'product_name': alert.product.name,
                'current_stock': alert.inventory.stock,
                'threshold': alert.threshold,
                'severity': alert.severity,
            })

        return items

    def validate_name(self, value):
        """
        Ensures no duplicate branch names.
        No choice restriction — business can expand to any city.
        """
        instance = getattr(self, 'instance', None)
        qs = Branch.objects.filter(name=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"A branch named '{value}' already exists."
            )
        return value

    def validate_manager_phone(self, value):
        """
        Validates manager phone follows Kenyan format.
        Must start with 07 or 01 and be 10 digits.
        """
        if not re.match(r'^(07|01)\d{8}$', value):
            raise serializers.ValidationError(
                "Manager phone must be 10 digits starting with 07 or 01."
            )
        return value
