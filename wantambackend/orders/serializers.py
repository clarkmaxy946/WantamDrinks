# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from branches.serializers import BranchSerializer
from products.serializers import ProductSerializer


class OrderItemInputSerializer(serializers.Serializer):
   
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    

    branch_id = serializers.CharField()
    items = OrderItemInputSerializer(many=True)

    def validate_branch_id(self, value):
        """
        Verifies the branch exists and is active.
        Inactive branches cannot receive orders.
        """
        from branches.models import Branch
        try:
            Branch.objects.get(branch_id=value, is_active=True)
        except Branch.DoesNotExist:
            raise serializers.ValidationError(
                f"Branch '{value}' does not exist or is not active."
            )
        return value

    def validate_items(self, value):
        
        if not value:
            raise serializers.ValidationError(
                "An order must contain at least one item."
            )

        # Check for duplicate products first
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Duplicate products found. "
                "Please combine quantities for the same product."
            )

        # ONE bulk query for all products instead of one per item
        from products.models import Product
        found_products = Product.objects.filter(
            product_id__in=product_ids
        ).values_list('product_id', flat=True)

        # Find any IDs not found in DB
        missing = set(product_ids) - set(found_products)
        if missing:
            raise serializers.ValidationError(
                f"The following products do not exist: {', '.join(missing)}"
            )

        return value


class OrderItemSerializer(serializers.ModelSerializer):
    

    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'product',
            'quantity',
            'price_at_purchase',    # Price snapshot — never changes
            'subtotal',             # quantity × price_at_purchase
        ]
        read_only_fields = fields

    def get_subtotal(self, obj):
        
        return obj.subtotal


class OrderSerializer(serializers.ModelSerializer):
    

    items = OrderItemSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_id',         # ORD-XXXXXX
            'customer',         # WNT-XXXXXX only — no sensitive data
            'branch',           # Full branch object
            'items',            # Full cart contents
            'total_price',      # Calculated in services.py
            'status',           # PENDING, COMPLETED, FAILED
            'transaction_id',   # M-Pesa receipt number
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_customer(self, obj):
        
        if obj.user:
            return obj.user.user_id
        return "Deleted User"


class AdminOrderSerializer(serializers.ModelSerializer):
    """
   

    Used in:
    - GET /api/admin/orders/                    → all orders
    - GET /api/admin/orders/<id>/               → single order detail
    - GET /api/admin/orders/?branch=BRN-NBI     → filter by branch
    - GET /api/admin/orders/?status=COMPLETED   → filter by status
    """

    items = OrderItemSerializer(many=True, read_only=True)
    branch = BranchSerializer(read_only=True)
    customer_id = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_id',
            'customer_id',          # WNT-XXXXXX
            'customer_email',       # For admin contact
            'customer_phone',       # For admin contact
            'branch',
            'items',
            'total_price',
            'status',
            'transaction_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_customer_id(self, obj):
        return obj.user.user_id if obj.user else "Deleted User"

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else "Deleted User"

    def get_customer_phone(self, obj):
        return obj.user.phone_number if obj.user else "Deleted User"
