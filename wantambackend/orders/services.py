# orders/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from inventory.models import Inventory
from analytics.services import update_sales_analytics


def place_order(user, branch, items):
    

    with transaction.atomic():

        product_ids = [item['product'].id for item in items]

        locked_inventory = Inventory.objects.select_for_update().filter(
            branch=branch,
            product_id__in=product_ids
        )

        inventory_map = {inv.product_id: inv for inv in locked_inventory}

       
        errors = []
        for item in items:
            product = item['product']
            quantity = item['quantity']
            inventory = inventory_map.get(product.id)

            if not inventory:
                errors.append(
                    f"{product.name} is not available at {branch.name}."
                )
                continue

            if inventory.stock < quantity:
                errors.append(
                    f"Not enough {product.name} at {branch.name}. "
                    f"Requested: {quantity}, Available: {inventory.stock}."
                )

        if errors:
            raise ValidationError(errors)

       
        total_price = sum(
            item['product'].price * item['quantity']
            for item in items
        )

        
        order = Order.objects.create(
            user=user,
            branch=branch,
            total_price=total_price,
            status=Order.Status.PENDING
        )

        
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price_at_purchase=item['product'].price  # Snapshot price now
            )

        # Stock is NOT touched. Waiting for M-Pesa confirmation.
        return order


def confirm_order(order, transaction_id):
    

    with transaction.atomic():

        
        if order.status != Order.Status.PENDING:
            raise ValidationError(
                f"Order {order.order_id} is already {order.status}. "
                f"Cannot process again."
            )

       
        items = order.items.select_related('product').all()
        product_ids = [item.product.id for item in items]

        locked_inventory = Inventory.objects.select_for_update().filter(
            branch=order.branch,
            product_id__in=product_ids
        )

        inventory_map = {inv.product_id: inv for inv in locked_inventory}

        
        errors = []
        for item in items:
            inventory = inventory_map.get(item.product.id)

            if not inventory or inventory.stock < item.quantity:
                available = inventory.stock if inventory else 0
                errors.append(
                    f"Stock changed for {item.product.name}. "
                    f"Requested: {item.quantity}, Available: {available}."
                )

        if errors:
            
            order.status = Order.Status.FAILED
            order.save()
            raise ValidationError(errors)

       
        for item in items:
            inventory = inventory_map[item.product.id]
            inventory.stock -= item.quantity
            inventory.save()

        
        order.status = Order.Status.COMPLETED
        order.transaction_id = transaction_id
        order.save()
        
        update_sales_analytics(order) 

        return order
