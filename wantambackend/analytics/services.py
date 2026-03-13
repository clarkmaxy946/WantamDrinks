# analytics/services.py
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import DailySalesReport, MonthlySalesReport


def update_sales_analytics(order):
   
    with transaction.atomic():

        # Get today's date and current month/year
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month

        
        for item in order.items.select_related('product', 'order__branch').all():

            branch = order.branch
            product = item.product
            quantity = item.quantity
            revenue = item.subtotal  
            daily_report, created = DailySalesReport.objects.get_or_create(
                branch=branch,
                product=product,
                date=today,
                defaults={
                    'total_sold': 0,
                    'total_revenue': 0.00
                }
            )

            DailySalesReport.objects.filter(
                branch=branch,
                product=product,
                date=today
            ).update(
                total_sold=F('total_sold') + quantity,
                total_revenue=F('total_revenue') + revenue
            )

           
            monthly_report, created = MonthlySalesReport.objects.get_or_create(
                branch=branch,
                product=product,
                year=current_year,
                month=current_month,
                defaults={
                    'total_sold': 0,
                    'total_revenue': 0.00
                }
            )

            MonthlySalesReport.objects.filter(
                branch=branch,
                product=product,
                year=current_year,
                month=current_month
            ).update(
                total_sold=F('total_sold') + quantity,
                total_revenue=F('total_revenue') + revenue
            )