# alerts/services.py
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import StockAlert


def resolve_alert(alert, resolved_by):
    
    if not resolved_by.is_staff:
        raise ValidationError("Only admin staff can resolve alerts.")

    
    if alert.is_resolved:
        raise ValidationError(
            f"Alert for {alert.product.name} at {alert.branch.name} "
            f"is already resolved."
        )
        
    inventory = alert.inventory
    inventory.refresh_from_db()  # Always get the latest stock value
 
    if inventory.stock <= inventory.low_stock_threshold:
        # Stock is still below threshold — block resolution
        # Tell the admin exactly what the situation is and where to restock
        raise ValidationError(
            {
                "error": "Cannot resolve alert — stock is still below threshold.",
                "current_stock": inventory.stock,
                "threshold": inventory.low_stock_threshold,
                "units_needed": inventory.low_stock_threshold - inventory.stock + 1,
                "restock_url": (
                    f"/api/admin/inventory/"
                    f"{alert.branch.branch_id}/"
                    f"{alert.product.product_id}/restock/"
                ),
            }
        )    

    
    alert.is_resolved = True
    alert.resolved_at = timezone.now()
    alert.resolved_by = resolved_by
    alert.save()

    return alert


def auto_resolve_alerts_for_inventory(inventory, resolved_by):
    
    if not resolved_by.is_staff:
        raise ValidationError("Only admin staff can resolve alerts.")

    
    unresolved_alerts = StockAlert.objects.filter(
        inventory=inventory,
        is_resolved=False
    )

    count = unresolved_alerts.count()

    
    if count == 0:
        return 0

    
    unresolved_alerts.update(
        is_resolved=True,
        resolved_at=timezone.now(),
        resolved_by=resolved_by
    )

    return count