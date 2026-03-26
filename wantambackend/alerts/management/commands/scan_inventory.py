from django.core.management.base import BaseCommand
from inventory.models import Inventory
from inventory.services import trigger_low_stock_alert
 
 
class Command(BaseCommand):
    help = (
        'Scans all inventory records and raises a StockAlert for any '
        'item whose stock is at or below its low_stock_threshold. '
        'Skips items that already have an open (unresolved) alert. '
        'Safe to run repeatedly — never creates duplicate alerts.'
    )
 
    def handle(self, *args, **options):
        self.stdout.write('Starting inventory scan...')
 
        # Fetch all inventory with branch and product in one query
        all_inventory = Inventory.objects.select_related(
            'branch',
            'product'
        ).all()
 
        total_scanned = 0
        total_alerted = 0
        total_skipped = 0  # Already had an open alert
 
        for inventory in all_inventory:
            total_scanned += 1
 
            if not inventory.is_low:
                # Stock is fine — nothing to do
                continue
 
            # Check if an unresolved alert already exists for this item
            from alerts.models import StockAlert
            already_alerted = StockAlert.objects.filter(
                inventory=inventory,
                is_resolved=False
            ).exists()
 
            if already_alerted:
                # Alert already open — skip silently
                total_skipped += 1
                continue
 
            # No open alert — create one now
            trigger_low_stock_alert(inventory)
            total_alerted += 1
 
            self.stdout.write(
                self.style.WARNING(
                    f'  ALERT created: {inventory.branch.name} | '
                    f'{inventory.product.name} | '
                    f'Stock: {inventory.stock} | '
                    f'Threshold: {inventory.low_stock_threshold}'
                )
            )
 
        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nScan complete. '
                f'Scanned: {total_scanned} | '
                f'New alerts: {total_alerted} | '
                f'Already alerted: {total_skipped}'
            )
        )
 