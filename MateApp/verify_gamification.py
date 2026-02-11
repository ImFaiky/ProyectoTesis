import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')
django.setup()

from users.models import CustomUser
from core.models import Discipline, Level, UserLevelProgress
from core.services import save_level_progress

def run_test():
    print("Creating test data...")
    # Create User
    user, _ = CustomUser.objects.get_or_create(username='testuser', defaults={'password': 'password'})
    # Reset points
    user.total_points = 0
    user.save()
    UserLevelProgress.objects.filter(user=user).delete() # Cleanup previous runs

    print(f"User created: {user} - Points: {user.total_points}")

    # Create Discipline
    math, _ = Discipline.objects.get_or_create(name='Math', defaults={'difficulty': 1})
    
    # Create Level
    level1, _ = Level.objects.get_or_create(discipline=math, number=1)
    
    # 1. Play Level 1 - Score 100
    print("1. Simulating Level 1 completion (Score: 100, Stars: 2)...")
    save_level_progress(user, level1, 100, 2)
    
    user.refresh_from_db()
    print(f"   User Points: {user.total_points} (Expected: 100)")
    assert user.total_points == 100

    # 2. Replay Level 1 - Lower Score 50
    print("2. Simulating Level 1 replay (Score: 50, Stars: 1)...")
    save_level_progress(user, level1, 50, 1)
    
    user.refresh_from_db()
    progress = UserLevelProgress.objects.get(user=user, level=level1)
    print(f"   User Points: {user.total_points} (Expected: 100)")
    print(f"   Level Score: {progress.score} (Expected: 100)")
    assert user.total_points == 100
    assert progress.score == 100
    assert progress.stars == 2

    # 3. Replay Level 1 - Higher Score 120
    print("3. Simulating Level 1 replay (Score: 120, Stars: 3)...")
    save_level_progress(user, level1, 120, 3)
    
    user.refresh_from_db()
    print(f"   User Points: {user.total_points} (Expected: 120)")
    assert user.total_points == 120

    print("SUCCESS: Logic for replaying levels verified.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
