# branches/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Branch
from .services import initialize_branch_inventory


@receiver(post_save, sender=Branch)
def on_branch_created(sender, instance, created, **kwargs):
    """
    Fires automatically after a Branch is saved.
    Only triggers on creation (not updates).
    Initializes inventory for all products at the new branch.
    """
    if created:
        initialize_branch_inventory(instance)