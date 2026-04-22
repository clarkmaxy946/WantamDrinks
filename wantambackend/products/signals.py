# products/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product


@receiver(post_save, sender=Product)
def on_product_created(sender, instance, created, **kwargs):
    """
    Fires automatically after a Product is saved.
    Only triggers on creation (not updates).
    Initializes a zero-stock inventory record for this product
    in every existing branch, so no branch is left without
    an inventory row for the new product.
    """
    if created:
        from inventory.services import initialize_product_inventory
        initialize_product_inventory(instance)