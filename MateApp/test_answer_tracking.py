import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.models import Level, UserLevelProgress
from core.views import play_level_simulation

User = get_user_model()

def test_tracking():
    # Setup
    student, _ = User.objects.get_or_create(username='student_test', email='test@example.com')
    if not student.check_password('pass'):
        student.set_password('pass')
        student.save()
        
    level = Level.objects.first()
    if not level:
        print("No levels found. Run setup_game_test.py first.")
        return

    # Simulate Answers
    answers = [
        {"question": "Q1", "user_answer": "4", "correct": True},
        {"question": "Q2", "user_answer": "Bad Answer", "correct": False}
    ]
    
    factory = RequestFactory()
    request = factory.post(f'/play/{level.id}/', {
        'score': 10,
        'stars': 1,
        'answers': json.dumps(answers)
    })
    request.user = student
    
    # Execute View
    response = play_level_simulation(request, level.id)
    
    # Verify
    progress = UserLevelProgress.objects.get(user=student, level=level)
    print(f"Progress Saved: Score={progress.score}, Stars={progress.stars}")
    print(f"Answers: {progress.answers}")
    
    if len(progress.answers) == 2 and progress.answers[1]['correct'] == False:
        print("SUCCESS: Answers tracked correctly.")
    else:
        print("FAILURE: Answers not tracked correctly.")

if __name__ == '__main__':
    test_tracking()
