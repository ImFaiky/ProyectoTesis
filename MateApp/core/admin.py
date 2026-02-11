from django.contrib import admin
from .models import Discipline, Level, UserLevelProgress

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'is_active')
    search_fields = ('name',)

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('discipline', 'number', 'is_active')
    list_filter = ('discipline',)
    ordering = ('discipline', 'number')

@admin.register(UserLevelProgress)
class UserLevelProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'score', 'stars', 'completed_at')
    list_filter = ('user', 'level__discipline')
