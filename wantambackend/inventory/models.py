# inventory/models.py
from django.db import models
from django.conf import settings
from branches.models import Branch
from products.models import Product


class Inventory(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="inventory_records",
        db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_records",
        db_index=True
    )
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"
        indexes = [
            models.Index(fields=["branch", "product"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "product"],
                name="unique_branch_product_inventory"
            )
        ]

    def __str__(self):
        return f"{self.branch.name} | {self.product.name} | Stock: {self.stock}"

    @property
    def is_low(self):
        return self.stock <= self.low_stock_threshold
    
    @property
    def is_in_stock(self):
        return self.stock > 0


class RestockLog(models.Model):
    
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,       # Never delete a log's inventory reference
        related_name='restock_logs'
    )
    restocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,      # Log survives even if user is deleted
        null=True,
        related_name='restock_logs'
    )
    quantity_added = models.PositiveIntegerField()
    stock_before = models.PositiveIntegerField()
    stock_after = models.PositiveIntegerField()
    restocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-restocked_at']
        indexes = [
            models.Index(fields=['restocked_at']),
            models.Index(fields=['inventory', 'restocked_at']),  # Audit queries
        ]

    def __str__(self):
        return (
            f"{self.inventory.branch.name} | "
            f"{self.inventory.product.name} | "
            f"+{self.quantity_added} units | "
            f"{self.restocked_at.strftime('%Y-%m-%d %H:%M')}"
        )