from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import UserLevelProgress

@receiver(post_save, sender=UserLevelProgress)
def update_user_points(sender, instance, created, **kwargs):
    user = instance.user
    # Calculate total points from all UserLevelProgress for this user
    total_score = UserLevelProgress.objects.filter(user=user).aggregate(
        total=Sum('score')
    )['total'] or 0
    
    user.total_points = total_score
    user.save()
