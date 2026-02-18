import os
import django
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')
django.setup()

User = get_user_model()

def verify_ui():
    client = Client()
    
    # Ensure admin user exists
    admin_user, _ = User.objects.get_or_create(username='admin_test', email='admin@test.com')
    if not admin_user.is_superuser:
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.set_password('adminpass')
        admin_user.save()
    
    client.force_login(admin_user)
    
    print("--- Verifying Discipline List UI ---")
    response = client.get(reverse('discipline_list'))
    content = response.content.decode('utf-8')
    if 'pagination' in content:
        print("✅ Pagination controls found.")
    else:
        print("⚠️ Pagination controls NOT found (might be due to few items).")
    if 'table-hover' in content:
        print("✅ Table styling found.")
        
    print("\n--- Verifying Student Create Form UI ---")
    response = client.get(reverse('student_create'))
    content = response.content.decode('utf-8')
    if 'card shadow' in content:
        print("✅ Card styling found.")
    else:
        print("❌ Card styling NOT found.")

    print("\n--- Verifying Level List UI ---")
    # Need a discipline ID
    from core.models import Discipline
    disc = Discipline.objects.first()
    if disc:
        response = client.get(reverse('level_list', kwargs={'discipline_id': disc.id}))
        content = response.content.decode('utf-8')
        if 'table-hover' in content:
            print("✅ Table styling found.")

if __name__ == '__main__':
    verify_ui()
