from django.db import models

class Branch(models.Model):
    branch_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    manager_name = models.CharField(max_length=100)
    manager_phone = models.CharField(max_length=15)
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)     

    def __str__(self):
        return f"{self.name} ({self.branch_id})"

    class Meta:
        verbose_name_plural = "Branches"