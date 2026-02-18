import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Discipline, Level

User = get_user_model()

def create_test_data():
    # 1. Create Student
    student, created = User.objects.get_or_create(username='student1', email='student1@example.com')
    if created:
        student.set_password('password123')
        student.save()
        print("Created student: student1 / password123")
    else:
        print("Student student1 already exists")

    # 2. Create Discipline
    # Note: Icon handling in script is tricky without actual files. 
    # We will just set color and name to verify the card rendering.
    math, _ = Discipline.objects.get_or_create(
        name='Mathematics', 
        defaults={
            'description': 'Math Basics', 
            'color': '#FF5733', 
            'difficulty': 1
        }
    )
    
    science, _ = Discipline.objects.get_or_create(
        name='Science', 
        defaults={
            'description': 'World of Science', 
            'color': '#28a745', 
            'difficulty': 2
        }
    )
    
    # 3. Create Level with Mixed Questions
    config = {
        "questions": [
            {
                "type": "option",
                "question": {
                    "text": "What is 2 + 2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": "4"
                }
            },
             {
                "type": "writing",
                "question": {
                    "text": "Spell 'Three'",
                    "correct_answer": "Three"
                }
            },
            {
                "type": "cards",
                "question": {
                     "text": "Choose the Apple",
                     "correct_answer": "Apple"
                },
                "options": [
                    {"text": "Apple", "icon": "https://img.icons8.com/color/96/apple.png"},
                    {"text": "Banana", "icon": "https://img.icons8.com/color/96/banana.png"}
                ]
            }
        ]
    }

    level, created = Level.objects.get_or_create(discipline=math, number=1)
    level.game_config = config
    level.is_active = True
    level.save()
    print(f"Created/Updated Level 1 for {math.name} with {len(config['questions'])} questions.")

if __name__ == '__main__':
    create_test_data()
