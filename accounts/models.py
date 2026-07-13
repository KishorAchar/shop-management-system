from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Station Commander'),
        ('manager', 'Sector Manager'),
        ('staff', 'Operations Officer'),
        ('customer', 'Global Citizen'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    avatar = models.CharField(max_length=2, default='👤')
    sector = models.CharField(max_length=50, default='Sector 1')
    dark_theme = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'accounts_user'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"