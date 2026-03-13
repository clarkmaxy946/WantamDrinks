# inventory/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Inventory, RestockLog


def add_stock(branch, product, quantity, restocked_by):
    
    if not restocked_by.is_staff:
        raise ValidationError("Only admin staff can restock inventory.")

    
    if quantity <= 0:
        raise ValidationError("Restock quantity must be a positive number.")

    with transaction.atomic():

       
        inventory, created = Inventory.objects.get_or_create(
            branch=branch,
            product=product,
            defaults={'stock': 0}
        )

       
        inventory = Inventory.objects.select_for_update().get(
            branch=branch,
            product=product
        )

        
        stock_before = inventory.stock

       
        inventory.stock += quantity
        inventory.save()

        
        RestockLog.objects.create(
            inventory=inventory,
            restocked_by=restocked_by,
            quantity_added=quantity,
            stock_before=stock_before,
            stock_after=inventory.stock
        )
        
        from alerts.services import auto_resolve_alerts_for_inventory
        auto_resolve_alerts_for_inventory(inventory, restocked_by)

        return inventory


def check_low_stock(inventory):
    

    if inventory.is_low:
        _trigger_low_stock_alert(inventory)
        return True
    return False


def _trigger_low_stock_alert(inventory):
    
    from alerts.models import StockAlert

    
    already_alerted = StockAlert.objects.filter(
        inventory=inventory,
        is_resolved=False
    ).exists()

    if not already_alerted:
        
        if inventory.stock <= 1:
            severity = StockAlert.Severity.CRITICAL
        else:
            severity = StockAlert.Severity.LOW
        
        StockAlert.objects.create(
            inventory=inventory,
            branch=inventory.branch,
            product=inventory.product,
            stock_at_alert=inventory.stock,
            threshold=inventory.low_stock_threshold
        )