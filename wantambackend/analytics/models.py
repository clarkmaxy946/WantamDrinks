from django.db import models
from branches.models import Branch
from products.models import Product


# Create your models here.

class DailySalesReport(models.Model):
    

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='daily_reports'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='daily_reports'
    )

    # The specific day this snapshot covers
    date = models.DateField(db_index=True)

    # How many units of this product were sold at this branch on this day
    total_sold = models.PositiveIntegerField(default=0)

    # Total revenue from this product at this branch on this day
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    # Timestamp for audit purposes
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            # Only one record per branch-product-date combination
            # Enforces the snapshot concept at DB level
            models.UniqueConstraint(
                fields=['branch', 'product', 'date'],
                name='unique_daily_report'
            )
        ]
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['branch', 'date']),    # "All Nairobi sales in March"
            models.Index(fields=['product', 'date']),   # "All Coke sales in March"
            models.Index(fields=['branch', 'product', 'date']),  # Most specific query
        ]

    def __str__(self):
        return (
            f"{self.branch.name} | {self.product.name} | "
            f"{self.date} | Sold: {self.total_sold} | "
            f"Revenue: KES {self.total_revenue}"
        )


class MonthlySalesReport(models.Model):
    

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='monthly_reports'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='monthly_reports'
    )

    # Year and month stored separately for easy filtering
    # e.g. filter(year=2025, month=3) for March 2025
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()  # 1=January, 12=December

    total_sold = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month']
        constraints = [
            # Only one record per branch-product-year-month combination
            models.UniqueConstraint(
                fields=['branch', 'product', 'year', 'month'],
                name='unique_monthly_report'
            )
        ]
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['branch', 'year', 'month']),
            models.Index(fields=['product', 'year', 'month']),
        ]

    def __str__(self):
        return (
            f"{self.branch.name} | {self.product.name} | "
            f"{self.year}-{str(self.month).zfill(2)} | "
            f"Sold: {self.total_sold} | "
            f"Revenue: KES {self.total_revenue}"
        )
     