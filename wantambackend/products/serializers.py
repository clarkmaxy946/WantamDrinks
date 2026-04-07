from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    price     = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['product_id', 'name', 'price', 'image_url']
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            path = f'/static/images/{obj.image}'
            return request.build_absolute_uri(path) if request else path
        return None


class AdminProductSerializer(serializers.ModelSerializer):
    price     = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['product_id', 'name', 'price', 'image', 'image_url']
        read_only_fields = []

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            path = f'/static/images/{obj.image}'
            return request.build_absolute_uri(path) if request else path
        return None

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than KES 0.00.")
        if value > 100000:
            raise serializers.ValidationError("Price cannot exceed KES 100,000. Please verify.")
        return value

    def validate_name(self, value):
        valid_choices = [choice[0] for choice in Product.SODA_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Invalid product. Must be one of: {', '.join(valid_choices)}."
            )
        return value