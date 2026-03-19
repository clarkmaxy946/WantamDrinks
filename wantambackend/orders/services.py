# orders/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from inventory.services import check_low_stock
from .models import Order, OrderItem
from inventory.models import Inventory
from analytics.services import update_sales_analytics


def place_order(user, branch, items):
    

    with transaction.atomic():

        product_ids = [item['product'].product_id for item in items]

        locked_inventory = Inventory.objects.select_for_update().filter(
            branch=branch,
            product_id__in=product_ids
        )

        inventory_map = {inv.product_id: inv for inv in locked_inventory}

        # Validate stock for all items
        errors = []
        for item in items:
            product = item['product']
            quantity = item['quantity']
            inventory = inventory_map.get(product.product_id)

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

        # Calculate total
        total_price = sum(
            item['product'].price * item['quantity']
            for item in items
        )

        # Create PENDING order
        order = Order.objects.create(
            user=user,
            branch=branch,
            total_price=total_price,
            status=Order.Status.PENDING
        )

        # Create order items and deduct stock immediately
        # Prevents overselling — stock is reserved for this order
        for item in items:
            product = item['product']
            quantity = item['quantity']
            inventory = inventory_map[product.product_id]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price  # Snapshot price now
            )

            # Deduct stock immediately on order creation
            inventory.stock -= quantity
            inventory.save()

            # Check if stock is low after deduction
            check_low_stock(inventory)

        return order


def confirm_order(order, transaction_id):
    

    with transaction.atomic():

        # Guard against double processing
        if order.status != Order.Status.PENDING:
            raise ValidationError(
                f"Order {order.order_id} is already {order.status}. "
                f"Cannot process again."
            )

        # Mark order as COMPLETED
        # Stock already deducted in place_order() — no deduction here
        order.status = Order.Status.COMPLETED
        order.transaction_id = transaction_id
        order.save()

        # Update analytics
        update_sales_analytics(order)

        return order


def restore_order_stock(order):
    

    with transaction.atomic():

        items = order.items.select_related('product').all()
        product_ids = [item.product.product_id for item in items]

        # Lock inventory rows before restoring
        locked_inventory = Inventory.objects.select_for_update().filter(
            branch=order.branch,
            product_id__in=product_ids
        )

        inventory_map = {inv.product_id: inv for inv in locked_inventory}

        # Restore stock for each item
        for item in items:
            inventory = inventory_map.get(item.product.product_id)
            if inventory:
                inventory.stock += item.quantity
                inventory.save()