import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from branches.models import Branch
from products.models import Product


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    order_id = models.CharField(
        max_length=15,
        unique=True,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Order survives user deletion
        null=True,
        related_name='orders'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="M-Pesa transaction reference"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['branch', 'created_at']),  # Analytics queries
            models.Index(fields=['user', 'created_at']),    # Purchase history
        ]

    def save(self, *args, **kwargs):
        if not self.order_id:
            while True:
                new_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
                if not Order.objects.filter(order_id=new_id).exists():
                    self.order_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        user_label = self.user.user_id if self.user else "Deleted User"
        return f"{self.order_id} | {user_label} | {self.status}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    price_at_purchase = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_product_per_order'
            )
        ]
        indexes = [
            models.Index(fields=['product']),
        ]

    @property
    def subtotal(self):
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.quantity}x {self.product.name} ({self.order.order_id})"
    