from django.db import models
from django.conf import settings

class Discipline(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    color = models.CharField(max_length=20, help_text="Hex color code")
    difficulty = models.IntegerField(default=1)
    icon = models.ImageField(upload_to='discipline_icons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_disciplines')

    def __str__(self):
        return self.name

class Level(models.Model):
    THEME_CHOICES = [
        ('none', 'Sin temática'),
        ('tortoise_hare', 'La Liebre y la Tortuga'),
        ('mountain_climb', 'Escalada de Montaña'),
    ]

    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='levels')
    number = models.IntegerField()
    game_config = models.JSONField(default=dict, blank=True, help_text="Specific configuration for the game in this level")
    is_active = models.BooleanField(default=True)
    assigned_students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='assigned_levels')
    theme = models.CharField(max_length=30, choices=THEME_CHOICES, default='none', help_text="Visual theme for the level gameplay")
    time_limit_seconds = models.IntegerField(default=300, help_text="Time limit in seconds (used by timed themes like Tortoise & Hare)")

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
    answers = models.JSONField(default=list, blank=True)
    attempts = models.IntegerField(default=0)
    best_time_seconds = models.IntegerField(null=True, blank=True, help_text="Best completion time in seconds")
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'level']

    def __str__(self):
        return f"{self.user.username} - {self.level} - Stars: {self.stars}"

    def save(self, *args, **kwargs):
        # Update user total points logic could be here or in a signal/service
        super().save(*args, **kwargs)


class QuestionImage(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='question_images', null=True, blank=True)
    image = models.ImageField(upload_to='question_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.level} - {self.image.name}"


class Classroom(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='classrooms')
    name = models.CharField(max_length=150, help_text="Classroom/group name")
    code = models.CharField(max_length=10, unique=True, help_text="Unique code for student enrollment")
    access_password = models.CharField(max_length=50, help_text="Access password for the classroom")
    description = models.TextField(blank=True, default='')
    disciplines = models.ManyToManyField('Discipline', blank=True, related_name='classrooms')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.teacher.username}"

    @property
    def student_count(self):
        return self.enrollments.count()


class ClassroomEnrollment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['classroom', 'student']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} → {self.classroom.name}"


class AIConversation(models.Model):
    PURPOSE_CHOICES = [
        ('tutor', 'Tutor IA (Estudiante)'),
        ('generate', 'Generar Preguntas (Profesor)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations')
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='tutor')
    prompt = models.TextField(help_text="Texto enviado por el usuario a la IA")
    response = models.TextField(help_text="Respuesta recibida de la IA")
    tokens_used = models.IntegerField(default=0, help_text="Tokens consumidos en esta interacción")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.purpose} - {self.created_at:%Y-%m-%d %H:%M}"


class LevelAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='level_attempts')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    stars = models.IntegerField(default=0)
    time_seconds = models.IntegerField(default=0, help_text="Time spent on this attempt in seconds")
    answers = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.level} - Attempt at {self.created_at:%Y-%m-%d %H:%M}"
