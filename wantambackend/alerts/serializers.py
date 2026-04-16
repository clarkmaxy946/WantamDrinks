# alerts/serializers.py
from rest_framework import serializers
from .models import StockAlert
from .services import resolve_alert


class StockAlertSerializer(serializers.ModelSerializer):
    """
    Used in:
    - GET /api/admin/alerts/                    → all alerts
    - GET /api/admin/alerts/?is_resolved=false  → active alerts only
    - GET /api/admin/alerts/?branch=BRN-NBI     → filter by branch
    - GET /api/admin/alerts/?product=Coke       → filter by product
    - GET /api/admin/alerts/<id>/               → single alert detail
    """

    # Context fields — readable strings instead of IDs
    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    # Current stock level from inventory
    # Shows admin how situation has changed since alert fired
    # e.g. alert fired at stock=2, admin restocked, now stock=50
    current_stock = serializers.SerializerMethodField()

    # Resolution info — who fixed it and when
    # Uses CustomUser.__str__ → "username (WNT-XXXXXX)"
    resolved_by = serializers.SerializerMethodField()

    class Meta:
        model = StockAlert
        fields = [
            'id',
            'branch_name',
            'branch_id',# "Nairobi" instead of BRN-NBI
            'product_name',         # "Coke" instead of PRD-001
            'stock_at_alert',       # Snapshot — what stock was when alert fired
            'threshold',            # Snapshot — what threshold was at alert time
            'current_stock',        # Live — current stock from inventory
            'severity',             # LOW or CRITICAL — for color coding
            'is_resolved',          # Primary filter for admin todo list
            'resolved_by',          # "john (WNT-A1B2C3)" or null
            'resolved_at',          # When it was resolved
            'created_at',           # When alert was triggered
        ]
        read_only_fields = fields

    def get_current_stock(self, obj):
       
        return obj.inventory.stock

    def get_resolved_by(self, obj):
       
        if obj.resolved_by:
            return str(obj.resolved_by)  # calls __str__ on CustomUser
        return None


class ResolveAlertSerializer(serializers.Serializer):
    

    def validate(self, attrs):
        
        request = self.context.get('request')
        alert = self.context.get('alert')

        # --- Staff only guard ---
        if not request.user.is_staff:
            raise serializers.ValidationError(
                "Only admin staff can resolve alerts."
            )

        # --- Already resolved guard ---
        if alert.is_resolved:
            raise serializers.ValidationError(
                f"Alert for {alert.product.name} at "
                f"{alert.branch.name} is already resolved."
            )

        return attrs

    def save(self):
        
        request = self.context.get('request')
        alert = self.context.get('alert')

        return resolve_alert(
            alert=alert,
            resolved_by=request.user
        )


class AlertSummarySerializer(serializers.Serializer):
    

    total_unresolved = serializers.IntegerField()
    critical_count = serializers.IntegerField()
    low_count = serializers.IntegerField()
    branches_affected = serializers.ListField(
        child=serializers.CharField()
    )
