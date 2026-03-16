# products/serializers.py
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Customer-facing product serializer.
    Read-only — customers can never modify product data.
    Only shows active-relevant fields needed for purchase decision.

    Used in:
    - GET /api/products/          → full product list
    - GET /api/inventory/<branch>/ → stock view per branch
    - GET /api/orders/             → order summary
    """

    # Always return price with exactly 2 decimal places
    # Ensures KES 150 displays as 150.00 not 150
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False  # Returns as number not string for frontend math
    )

    class Meta:
        model = Product
        fields = [
            'product_id',   # e.g. PRD-001 — needed for order placement
            'name',         # Coke, Fanta, Sprite
            'price',        # KES 150.00
        ]
        read_only_fields = fields   # Entire serializer is read-only for customers


class AdminProductSerializer(serializers.ModelSerializer):
    """
    Admin-facing product serializer.
    Allows admin to create and update products.
    Enforces price integrity rules.

    Used in:
    - GET    /api/admin/products/           → full product list
    - POST   /api/admin/products/           → create new product
    - PATCH  /api/admin/products/<id>/      → update price
    """

    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False
    )

    class Meta:
        model = Product
        fields = [
            'product_id',
            'name',
            'price',
        ]
        read_only_fields = ['product_id']   # Auto-generated — never editable

    def validate_price(self, value):
        """
        Financial integrity check.
        Prevents zero or negative prices from entering the system.
        Critical because Orders multiply this price by quantity.
        A wrong price here breaks total_revenue in analytics.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than KES 0.00."
            )
        if value > 100000:
            raise serializers.ValidationError(
                "Price cannot exceed KES 100,000. Please verify."
            )
        return value

    def validate_name(self, value):
        """
        Ensures only the three defined soda types can be created.
        Choices are enforced at model level but we add a cleaner
        API error message here.
        """
        valid_choices = [choice[0] for choice in Product.SODA_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Invalid product. Must be one of: {', '.join(valid_choices)}."
            )
        return value
