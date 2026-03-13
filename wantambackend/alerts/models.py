from django.db import models
from django.conf import settings
from inventory.models import Inventory
from branches.models import Branch
from products.models import Product

# Create your models here.

class StockAlert(models.Model):

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'           # Stock is approaching threshold
        CRITICAL = 'CRITICAL', 'Critical'  # Stock is at or near zero

    # --- What triggered the alert ---
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    # --- Snapshot data at time of alert ---
    # We store these directly so the alert is self-contained.
    # Even if inventory changes after the alert, you can see
    # exactly what the stock was when the alert fired.
    stock_at_alert = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.LOW
    )

    # --- Resolution tracking ---
    is_resolved = models.BooleanField(
        default=False,
        db_index=True   # Queried constantly — filter(is_resolved=False)
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_resolved']),
            models.Index(fields=['branch', 'is_resolved']),    # Admin filters by branch
            models.Index(fields=['product', 'is_resolved']),   # Admin filters by product
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        status = "RESOLVED" if self.is_resolved else "UNRESOLVED"
        return (
            f"[{self.severity}] {self.branch.name} | "
            f"{self.product.name} | "
            f"Stock: {self.stock_at_alert} | "
            f"{status}"
        )