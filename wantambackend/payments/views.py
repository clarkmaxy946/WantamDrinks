# payments/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Payment
from .serializers import (
    InitiatePaymentSerializer,
    PaymentStatusSerializer,
    AdminPaymentSerializer,
)
from django.db import transaction
from orders.services import restore_order_stock
from .services import initiate_stk_push, process_mpesa_callback
from orders.models import Order


class InitiatePaymentView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the order — already validated in serializer
        order = Order.objects.get(
            order_id=serializer.validated_data['order_id']
        )
        phone_number = serializer.validated_data['phone_number']

        # Call service to initiate STK push
        try:
            payment = initiate_stk_push(
                order=order,
                phone_number=phone_number
            )
        except ValidationError as e:
            return Response(
                {"error": e.messages if hasattr(e, 'messages') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "M-Pesa prompt sent to your phone. "
                           "Please enter your PIN to complete payment.",
                "payment_id": payment.payment_id,
                "order_id": order.order_id,
                "amount": payment.amount,
            },
            status=status.HTTP_200_OK
        )

@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        # Pass raw JSON directly to service — no serializer needed
        # Safaricom's JSON structure is handled internally
        process_mpesa_callback(request.data)

        # Always return 200 to Safaricom
        # If we return anything else, Safaricom will keep retrying
        return Response(
            {"ResultCode": 0, "ResultDesc": "Accepted"},
            status=status.HTTP_200_OK
        )


class PaymentStatusView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.select_related(
                'order',
                'user'
            ).get(payment_id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": f"Payment '{payment_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Customer can only view their own payment
        if payment.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You can only view your own payment status."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PaymentStatusSerializer(payment)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class CustomerPaymentHistoryView(APIView):
    """
    GET /api/payments/history/
    Protected — requires JWT token.
    Customer views their own payment history.
    Most recent payments first.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(
            user=request.user
        ).select_related(
            'order__branch'
        ).order_by('-created_at')

        serializer = PaymentStatusSerializer(payments, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminPaymentListView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        payments = Payment.objects.select_related(
            'order__branch',
            'user'
        ).order_by('-created_at')

        # Filter by status
        payment_status = request.query_params.get('status')
        if payment_status:
            payments = payments.filter(
                status=payment_status.upper()
            )

        # Filter by branch
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            payments = payments.filter(
                order__branch__branch_id=branch_id
            )

        # Filter by date
        date = request.query_params.get('date')
        if date:
            payments = payments.filter(created_at__date=date)

        serializer = AdminPaymentSerializer(payments, many=True)
        data = serializer.data
        return Response(
            {
                "total_payments": len(data),
                "payments": data
            },
            status=status.HTTP_200_OK
        )


class AdminPaymentDetailView(APIView):
   
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.select_related(
                'order__branch',
                'user'
            ).get(payment_id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": f"Payment '{payment_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminPaymentSerializer(payment)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
class TimeoutPaymentView(APIView):
    """
    POST /api/payments/<payment_id>/timeout/
    Called by the frontend when polling expires without a Safaricom callback.
    Only acts if payment is still PENDING — ignores SUCCESS/FAILED/CANCELLED.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.select_related(
                'order', 'user'
            ).get(payment_id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": f"Payment '{payment_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only the owner can timeout their own payment
        if payment.user != request.user:
            return Response(
                {"error": "You can only timeout your own payments."},
                status=status.HTTP_403_FORBIDDEN
            )

        # If Safaricom already responded, do nothing — return current state
        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "message": f"Payment is already {payment.status}. No changes made.",
                    "status": payment.status,
                },
                status=status.HTTP_200_OK
            )

        # Payment is still PENDING — mark it failed and restore stock
        with transaction.atomic():
            payment.status = Payment.Status.FAILED
            payment.failure_reason = "Payment timed out — no response from Safaricom."
            payment.save()

            # Restore reserved stock back to inventory
            restore_order_stock(payment.order)

            # Mark order as FAILED
            order = payment.order
            order.status = Order.Status.FAILED
            order.save()

        return Response(
            {
                "message": "Payment marked as timed out. Stock has been restored.",
                "status": payment.status,
            },
            status=status.HTTP_200_OK
        )
class AdminCancelPaymentView(APIView):
    """
    POST /api/admin/payments/<payment_id>/cancel/
    Admin-only. Cancels a PENDING payment and marks its order as FAILED,
    restoring stock. Has no effect on SUCCESS/FAILED/CANCELLED payments.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.select_related(
                'order', 'user'
            ).get(payment_id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": f"Payment '{payment_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "error": f"Payment is already {payment.status}. "
                             f"Only PENDING payments can be cancelled."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            payment.status = Payment.Status.CANCELLED
            payment.failure_reason = f"Cancelled by admin: {request.user.username}"
            payment.save()

            restore_order_stock(payment.order)

            order = payment.order
            order.status = Order.Status.FAILED
            order.save()

        return Response(
            {
                "message": f"Payment '{payment_id}' cancelled. "
                           f"Order '{order.order_id}' marked as failed. "
                           f"Stock restored.",
                "payment_id": payment.payment_id,
                "order_id": order.order_id,
                "payment_status": payment.status,
                "order_status": order.status,
            },
            status=status.HTTP_200_OK
        )
            