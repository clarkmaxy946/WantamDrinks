# payments/models.py
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from orders.models import Order

phone_validator = RegexValidator(
    regex=r'^(07|01)\d{8}$',
    message="Phone number must be 10 digits starting with 07 or 01."
)


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    payment_id = models.CharField(
        max_length=15,
        unique=True,
        editable=False
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='payment'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments'
    )
    phone_number = models.CharField(
        max_length=10,
        validators=[phone_validator]
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    checkout_request_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="M-Pesa STK push identifier"
    )
    merchant_request_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="M-Pesa merchant request identifier"
    )
    receipt_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        help_text="M-Pesa receipt number after successful payment"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )

    # JSONField — structured, queryable, inspectable
    raw_callback = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw M-Pesa callback response for debugging"
    )
    
    failure_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Safaricom failure description for failed payments"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['receipt_number']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        """
        Validates payment amount matches order total exactly.
        Prevents partial payments from reaching M-Pesa.
        """
        if self.order and self.amount != self.order.total_price:
            raise ValidationError(
                f"Payment amount (KES {self.amount}) does not match "
                f"order total (KES {self.order.total_price})."
            )

    def save(self, *args, **kwargs):
        # Run clean() validation before every save
        self.full_clean()
        if not self.payment_id:
            while True:
                new_id = f"PAY-{uuid.uuid4().hex[:6].upper()}"
                if not Payment.objects.filter(payment_id=new_id).exists():
                    self.payment_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.payment_id} | "
            f"Order: {self.order.order_id} | "
            f"KES {self.amount} | "
            f"{self.status}"
        )