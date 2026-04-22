# products/serializers.py
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
        read_only_fields = ['product_id']  # auto-generated on save, never set by client

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            path = f'/static/images/{obj.image}'
            return request.build_absolute_uri(path) if request else path
        return None

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Product name must be at least 2 characters.")
        if len(value) > 20:
            raise serializers.ValidationError("Product name cannot exceed 20 characters.")
        # Check uniqueness, excluding the current instance on updates
        qs = Product.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"A product named '{value}' already exists.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than KES 0.00.")
        if value > 100000:
            raise serializers.ValidationError("Price cannot exceed KES 100,000. Please verify.")
        return value

    def validate_image(self, value):
        if value and len(value) > 100:
            raise serializers.ValidationError("Image filename cannot exceed 100 characters.")
        return value.strip() if value else ''