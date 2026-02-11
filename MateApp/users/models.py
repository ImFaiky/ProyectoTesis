from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    total_points = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1) # Simplified tracking
    
    
    def __str__(self):
        return self.username
