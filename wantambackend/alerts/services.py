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