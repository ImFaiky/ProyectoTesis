import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create Game Admin (Teacher)
if not User.objects.filter(username='teacher').exists():
    User.objects.create_user('teacher', 'teacher@example.com', 'teacher', role=2)
    print("User 'teacher' (Role: Admin) created with password 'teacher'")
else:
    print("User 'teacher' already exists")

# Create Student
if not User.objects.filter(username='student').exists():
    User.objects.create_user('student', 'student@example.com', 'student', role=3)
    print("User 'student' (Role: Student) created with password 'student'")
else:
    print("User 'student' already exists")
