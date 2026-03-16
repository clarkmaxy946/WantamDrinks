from django.db import transaction
from .models import Branch
from products.models import Product
from inventory.models import Inventory


def initialize_branch_inventory(branch):
    

    products = Product.objects.all()
    created_records = []

    with transaction.atomic():
        for product in products:
            inventory, created = Inventory.objects.get_or_create(
                branch=branch,
                product=product,
                defaults={'stock': 0}
            )
            if created:
                created_records.append(inventory)

    return created_records


def get_active_branches():
    
    return Branch.objects.filter(is_active=True).order_by('name')