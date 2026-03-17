# payments/serializers.py
from rest_framework import serializers
from .models import Payment
from orders.models import Order


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Used in:
    - POST /api/payments/initiate/
    """

    order_id = serializers.CharField()
    phone_number = serializers.CharField(max_length=10)

    def validate_order_id(self, value):
       
        try:
            Order.objects.get(order_id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError(
                f"Order '{value}' does not exist."
            )
        return value

    def validate_phone_number(self, value):
        
        import re
        if not re.match(r'^(07|01)\d{8}$', value):
            raise serializers.ValidationError(
                "Phone number must be 10 digits starting with 07 or 01."
            )
        return value

    def validate(self, attrs):
        
        order_id = attrs.get('order_id')
        request = self.context.get('request')

        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            # Already caught in validate_order_id
            return attrs

        # --- Order ownership check ---
        # Customer can only pay for their own orders
        if order.user != request.user:
            raise serializers.ValidationError({
                'order_id': "You can only pay for your own orders."
            })

        # --- Order state machine check ---
        # COMPLETED order — already paid, no retry needed
        if order.status == Order.Status.COMPLETED:
            raise serializers.ValidationError({
                'order_id': (
                    f"Order {order_id} is already completed. "
                    f"No payment needed."
                )
            })

        # FAILED order — must place a new order, cannot retry payment
        if order.status == Order.Status.FAILED:
            raise serializers.ValidationError({
                'order_id': (
                    f"Order {order_id} has failed. "
                    f"Please place a new order."
                )
            })

        # --- Existing payment state check ---
        if hasattr(order, 'payment'):
            existing_payment = order.payment

            # Payment in progress — do not send another STK push
            if existing_payment.status == Payment.Status.PENDING:
                raise serializers.ValidationError({
                    'order_id': (
                        "A payment is already in progress for this order. "
                        "Please check your phone for the M-Pesa prompt."
                    )
                })

            # Previous payment succeeded — no retry needed
            if existing_payment.status == Payment.Status.SUCCESS:
                raise serializers.ValidationError({
                    'order_id': (
                        f"Order {order_id} has already been paid. "
                        f"Receipt: {existing_payment.receipt_number}"
                    )
                })

            # FAILED or CANCELLED payment — retry is allowed
            # initiate_stk_push() will create a new Payment record

        return attrs


class PaymentStatusSerializer(serializers.ModelSerializer):
    """
    Used in:
    - GET /api/payments/<payment_id>/status/
    """

    # Human readable message based on current status
    status_message = serializers.SerializerMethodField()

    # Order reference for context
    order_id = serializers.CharField(
        source='order.order_id',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'payment_id',
            'order_id',
            'amount',
            'status',
            'status_message',   # Dynamic feedback to customer
            'receipt_number',   # Only populated on SUCCESS
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_status_message(self, obj):
       
        messages = {
            Payment.Status.PENDING: (
                "Awaiting M-Pesa PIN entry. "
                "Please check your phone."
            ),
            Payment.Status.SUCCESS: (
                f"Payment successful. "
                f"Receipt: {obj.receipt_number}"
            ),
            Payment.Status.FAILED: (
                "Payment failed. "
                f"{obj.failure_reason or 'Please try again.'}"
            ),
            Payment.Status.CANCELLED: (
                "Payment was cancelled. "
                "You can retry by initiating a new payment."
            ),
        }
        return messages.get(obj.status, "Unknown payment status.")


class AdminPaymentSerializer(serializers.ModelSerializer):
    """
    

    Used in:
    - GET /api/admin/payments/                      → all payments
    - GET /api/admin/payments/<id>/                 → single payment
    - GET /api/admin/payments/?status=FAILED        → filter by status
    - GET /api/admin/payments/?branch=BRN-NBI       → filter by branch
    """

    # Order details
    order_id = serializers.CharField(
        source='order.order_id',
        read_only=True
    )
    order_branch = serializers.CharField(
        source='order.branch.name',
        read_only=True
    )

    # Customer details
    customer_id = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'payment_id',
            'order_id',
            'order_branch',
            'customer_id',
            'customer_email',
            'phone_number',
            'amount',
            'status',
            'checkout_request_id',
            'merchant_request_id',
            'receipt_number',
            'failure_reason',       # Populated on FAILED payments
            'raw_callback',         # Full Safaricom response for debugging
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_customer_id(self, obj):
        return obj.user.user_id if obj.user else "Deleted User"

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else "Deleted User"
