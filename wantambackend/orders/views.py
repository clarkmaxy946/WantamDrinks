# orders/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError
from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    AdminOrderSerializer,
)
from .services import place_order, restore_order_stock
from branches.models import Branch
from products.models import Product


class OrderCreateView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get branch from validated data
        try:
            branch = Branch.objects.get(
                branch_id=serializer.validated_data['branch_id'],
                is_active=True
            )
        except Branch.DoesNotExist:
            return Response(
                {"error": "Branch not found or inactive."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Build items list with product objects
        # Price fetched from DB — never from request
        items = []
        for item in serializer.validated_data['items']:
            try:
                product = Product.objects.get(
                    product_id=item['product_id']
                )
                items.append({
                    'product': product,
                    'quantity': item['quantity']
                })
            except Product.DoesNotExist:
                return Response(
                    {"error": f"Product '{item['product_id']}' not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Call place_order service
        # Handles: stock validation, order creation,
        # price snapshot, immediate stock deduction
        try:
            order = place_order(
                user=request.user,
                branch=branch,
                items=items
            )
        except ValidationError as e:
            return Response(
                {"error": e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Order placed successfully. Proceed to payment.",
                "data": OrderSerializer(order).data
            },
            status=status.HTTP_201_CREATED
        )


class OrderHistoryView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related(
            'items__product'
        ).select_related(
            'branch'
        ).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class OrderDetailView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related(
                'items__product'
            ).select_related(
                'branch'
            ).get(
                order_id=order_id,
                user=request.user  # Ensures customer owns this order
            )
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order '{order_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class OrderCancelView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order '{order_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ownership check
        if not request.user.is_staff and order.user != request.user:
            return Response(
                {"error": "You can only cancel your own orders."},
                status=status.HTTP_403_FORBIDDEN
            )

        if order.status == Order.Status.COMPLETED:
            return Response(
                {
                    "error": f"Order '{order_id}' is already completed. "
                             f"Cannot cancel a paid order."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status == Order.Status.FAILED:
            return Response(
                {
                    "error": f"Order '{order_id}' has already failed. "
                             f"No cancellation needed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restore stock before cancelling
        # Stock was deducted in place_order() — must be restored
        restore_order_stock(order)

        # Mark order as FAILED
        order.status = Order.Status.FAILED
        order.save()

        return Response(
            {
                "message": f"Order '{order_id}' cancelled successfully. "
                           f"Stock has been restored.",
                "order_id": order.order_id,
                "status": order.status
            },
            status=status.HTTP_200_OK
        )


class AdminOrderListView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        orders = Order.objects.select_related(
            'user',
            'branch'
        ).prefetch_related(
            'items__product'
        ).order_by('-created_at')

        # Filter by branch
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            orders = orders.filter(branch__branch_id=branch_id)

        # Filter by status
        order_status = request.query_params.get('status')
        if order_status:
            orders = orders.filter(status=order_status.upper())

        # Filter by date
        date = request.query_params.get('date')
        if date:
            orders = orders.filter(created_at__date=date)

        serializer = AdminOrderSerializer(orders, many=True)
        data = serializer.data
        return Response(
            {
                "total_orders": len(data),
                "orders": data
            },
            status=status.HTTP_200_OK
        )


class AdminOrderDetailView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, order_id):
        try:
            order = Order.objects.select_related(
                'user',
                'branch'
            ).prefetch_related(
                'items__product'
            ).get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order '{order_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminOrderSerializer(order)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
