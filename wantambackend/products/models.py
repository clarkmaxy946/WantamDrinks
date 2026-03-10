from django.db import models

# Create your models here.
class Product(models.Model):
    SODA_CHOICES = [
        ('Coke', 'Coke'),
        ('Fanta', 'Fanta'),
        ('Sprite', 'Sprite'),
    ]
    product_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=20, choices=SODA_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name