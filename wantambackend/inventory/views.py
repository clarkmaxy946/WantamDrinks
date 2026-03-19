# inventory/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Prefetch
from .models import Inventory, RestockLog
from .serializers import (
    InventorySerializer,
    AdminInventorySerializer,
    RestockSerializer,
    RestockLogSerializer,
)
from .services import add_stock
from branches.models import Branch
from products.models import Product


class BranchInventoryView(APIView):
    
    permission_classes = [AllowAny]

    def get(self, request, branch_id):
        try:
            branch = Branch.objects.get(
                branch_id=branch_id,
                is_active=True
            )
        except Branch.DoesNotExist:
            return Response(
                {"error": f"Branch '{branch_id}' not found or inactive."},
                status=status.HTTP_404_NOT_FOUND
            )

        inventory = Inventory.objects.select_related(
            'branch',
            'product'
        ).filter(branch=branch)

        serializer = InventorySerializer(inventory, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminInventoryListView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        inventory = Inventory.objects.select_related(
            'branch',
            'product'
        ).prefetch_related(
            Prefetch(
                'restock_logs',
                queryset=RestockLog.objects.order_by('-restocked_at')
            )
        ).all()

        serializer = AdminInventorySerializer(inventory, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminLowStockView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        inventory = Inventory.objects.select_related(
            'branch',
            'product'
        ).all()

        # Filter using is_low property
        low_stock = [item for item in inventory if item.is_low]

        # Sort by stock level — lowest first
        low_stock.sort(key=lambda x: x.stock)

        serializer = AdminInventorySerializer(low_stock, many=True)
        return Response(
            {
                "total_low_stock": len(low_stock),
                "items": serializer.data
            },
            status=status.HTTP_200_OK
        )


class AdminBranchInventoryView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, branch_id):
        try:
            branch = Branch.objects.get(branch_id=branch_id)
        except Branch.DoesNotExist:
            return Response(
                {"error": f"Branch '{branch_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        inventory = Inventory.objects.select_related(
            'branch',
            'product'
        ).prefetch_related(
            Prefetch(
                'restock_logs',
                queryset=RestockLog.objects.order_by('-restocked_at')
            )
        ).filter(branch=branch)

        serializer = AdminInventorySerializer(inventory, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminInventoryDetailView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_inventory(self, branch_id, product_id):
        try:
            return Inventory.objects.select_related(
                'branch', 'product'
            ).get(
                branch__branch_id=branch_id,
                product__product_id=product_id
            )
        except Inventory.DoesNotExist:
            return None

    def patch(self, request, branch_id, product_id):
        inventory = self.get_inventory(branch_id, product_id)
        if not inventory:
            return Response(
                {"error": f"Inventory record not found for "
                          f"branch '{branch_id}' and product '{product_id}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only allow threshold update
        allowed_fields = {'low_stock_threshold'}
        invalid_fields = set(request.data.keys()) - allowed_fields
        if invalid_fields:
            return Response(
                {
                    "error": f"Only 'low_stock_threshold' can be updated. "
                             f"Invalid fields: {', '.join(invalid_fields)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AdminInventorySerializer(
            inventory,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Threshold updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminRestockView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, branch_id, product_id):
        serializer = RestockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            branch = Branch.objects.get(branch_id=branch_id)
        except Branch.DoesNotExist:
            return Response(
                {"error": f"Branch '{branch_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": f"Product '{product_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        inventory = add_stock(
            branch=branch,
            product=product,
            quantity=serializer.validated_data['quantity'],
            restocked_by=request.user
        )

        return Response(
            {
                "message": f"Successfully added "
                           f"{serializer.validated_data['quantity']} units of "
                           f"{product.name} to {branch.name}.",
                "current_stock": inventory.stock,
                "branch": branch.name,
                "product": product.name,
            },
            status=status.HTTP_200_OK
        )


class AdminRestockLogView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        logs = RestockLog.objects.select_related(
            'inventory__branch',
            'inventory__product',
            'restocked_by'
        ).order_by('-restocked_at')

        # Filter by branch if provided
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            logs = logs.filter(
                inventory__branch__branch_id=branch_id
            )

        # Filter by product if provided
        product_id = request.query_params.get('product_id')
        if product_id:
            logs = logs.filter(
                inventory__product__product_id=product_id
            )

        serializer = RestockLogSerializer(logs, many=True)
        return Response(
            {
                "total_logs": len(serializer.data),
                "logs": serializer.data
            },
            status=status.HTTP_200_OK
        )