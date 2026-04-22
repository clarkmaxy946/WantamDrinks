# products/models.py
from django.db import models


class Product(models.Model):
    product_id = models.CharField(max_length=10, primary_key=True, editable=False)
    name       = models.CharField(max_length=20, unique=True)
    price      = models.DecimalField(max_digits=10, decimal_places=2)
    image      = models.CharField(
                     max_length=100,
                     blank=True,
                     default='',
                     help_text="Filename only e.g. fanta.png — file must exist in static/images/"
                 )

    def _generate_product_id(self):
        """
        Derive product_id from the first 2 letters of the product name (uppercased)
        followed by a zero-padded 3-digit sequence number.

        Example:
            First "Coke"       → CO001
            Second "Cordial"   → CO002
            First "Fanta"      → FA001
        """
        prefix = self.name[:2].upper()

        # Find all existing product_ids that start with this prefix
        existing = (
            Product.objects.filter(product_id__startswith=prefix)
            .values_list('product_id', flat=True)
        )

        # Extract the numeric suffixes and find the next available number
        max_seq = 0
        for pid in existing:
            try:
                seq = int(pid[len(prefix):])
                if seq > max_seq:
                    max_seq = seq
            except ValueError:
                pass

        return f"{prefix}{max_seq + 1:03d}"

    def save(self, *args, **kwargs):
        # Only generate a product_id for new instances (no pk yet)
        if not self.product_id:
            self.product_id = self._generate_product_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name