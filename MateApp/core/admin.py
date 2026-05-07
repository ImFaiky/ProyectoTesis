from django.contrib import admin
from .models import Discipline, Level, UserLevelProgress, Classroom, ClassroomEnrollment

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

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active', 'teacher')
    search_fields = ('name', 'code')

@admin.register(ClassroomEnrollment)
class ClassroomEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'enrolled_at')
    list_filter = ('classroom',)
    search_fields = ('student__username', 'classroom__name')
