import re
from django.core.exceptions import ValidationError

class WantamPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_]', password):
            raise ValidationError("Password must contain at least one special character.")

    def get_help_text(self):
        return "Your password must be 8+ characters and include uppercase, lowercase, numbers, and special symbols."