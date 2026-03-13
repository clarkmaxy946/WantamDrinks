import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# --- VALIDATORS ---

# Phone Validator: 10 digits, starts with 07 or 01
phone_validator = RegexValidator(
    regex=r'^(07|01)\d{8}$',
    message="Phone number must be 10 digits starting with 07 or 01."
)

# Gmail Validator: Strictly @gmail.com
def validate_gmail(value):
    if not value.endswith('@gmail.com'):
        raise ValidationError("Only @gmail.com email addresses are allowed.")

# --- MODEL ---

class CustomUser(AbstractUser):
    # Custom ID field
    user_id = models.CharField(max_length=15, unique=True, editable=False)
    
    # Email as the unique identifier
    email = models.EmailField(
        unique=True, 
        validators=[validate_gmail],
        error_messages={
            'unique': "A user with that email already exists.",
        }
    )
    
    phone_number = models.CharField(
        max_length=10, 
        validators=[phone_validator], 
        unique=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    # Login configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number']

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def save(self, *args, **kwargs):
        # Generate a unique WNT-ID if it doesn't exist
        if not self.user_id:
            while True:
                new_id = f"WNT-{uuid.uuid4().hex[:6].upper()}"
                if not CustomUser.objects.filter(user_id=new_id).exists():
                    self.user_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.user_id})"