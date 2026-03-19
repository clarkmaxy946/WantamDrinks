# products/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import Product
from .serializers import ProductSerializer, AdminProductSerializer


class ProductListView(APIView):
    """
    GET /api/products/
    Public — no token required.
    Returns all products with current prices.
    Customer uses this to see what sodas are available
    and their prices before selecting quantity.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class ProductDetailView(APIView):
    """
    GET /api/products/<product_id>/
    Public — no token required.
    Returns single product details.
    """
    permission_classes = [AllowAny]

    def get_product(self, product_id):
        try:
            return Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return None

    def get(self, request, product_id):
        product = self.get_product(product_id)
        if not product:
            return Response(
                {"error": f"Product '{product_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminProductListView(APIView):
    """
    GET  /api/admin/products/ → admin sees all products
    POST /api/admin/products/ → admin creates new product
    Admin only — requires is_staff=True.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        products = Product.objects.all()
        serializer = AdminProductSerializer(products, many=True)
        data = serializer.data
        return Response(
            {
                "total_products": len(data),
                "products": data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = AdminProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(
                {
                    "message": f"Product '{product.name}' created successfully.",
                    "data": AdminProductSerializer(product).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminProductDetailView(APIView):
    """
    GET    /api/admin/products/<product_id>/ → single product detail
    PATCH  /api/admin/products/<product_id>/ → update product price
    DELETE /api/admin/products/<product_id>/ → delete product
    Admin only — requires is_staff=True.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_product(self, product_id):
        try:
            return Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return None

    def get(self, request, product_id):
        product = self.get_product(product_id)
        if not product:
            return Response(
                {"error": f"Product '{product_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminProductSerializer(product)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, product_id):
        product = self.get_product(product_id)
        if not product:
            return Response(
                {"error": f"Product '{product_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminProductSerializer(
            product,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": f"Product '{product_id}' updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, product_id):
        product = self.get_product(product_id)
        if not product:
            return Response(
                {"error": f"Product '{product_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent deletion if product has order history
        # Deleting would break order records and analytics
        if product.order_items.exists():
            return Response(
                {
                    "error": f"Product '{product.name}' has existing orders. "
                             f"Cannot delete a product with order history."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        product_name = product.name
        product.delete()
        return Response(
            {"message": f"Product '{product_name}' deleted successfully."},
            status=status.HTTP_200_OK
        )