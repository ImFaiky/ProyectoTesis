from django.db import models
from django.conf import settings

class Discipline(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    color = models.CharField(max_length=20, help_text="Hex color code")
    difficulty = models.IntegerField(default=1)
    icon = models.ImageField(upload_to='discipline_icons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Level(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='levels')
    number = models.IntegerField()
    game_config = models.JSONField(default=dict, blank=True, help_text="Specific configuration for the game in this level")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['discipline', 'number']
        unique_together = ['discipline', 'number']

    def __str__(self):
        return f"{self.discipline.name} - Level {self.number}"

class UserLevelProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='level_progress')
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    stars = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'level']

    def __str__(self):
        return f"{self.user.username} - {self.level} - Stars: {self.stars}"

    def save(self, *args, **kwargs):
        # Update user total points logic could be here or in a signal/service
        super().save(*args, **kwargs)
