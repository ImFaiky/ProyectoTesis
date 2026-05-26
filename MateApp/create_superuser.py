import os
import sys

# =========================================================================
# ACTIVACIÓN DINÁMICA DEL ENTORNO VIRTUAL EN CPANEL
# =========================================================================
venv_base = '/home/damisoft/virtualenv'
activate_script = None

if os.path.exists(venv_base):
    for root_dir, dirs, files in os.walk(venv_base):
        if 'activate_this.py' in files and 'mate-ia.damisoft-ec.com' in root_dir:
            activate_script = os.path.join(root_dir, 'activate_this.py')
            break

if activate_script:
    print(f"Activando entorno virtual: {activate_script}")
    with open(activate_script) as f:
        exec(f.read(), dict(__file__=activate_script))
else:
    print("ADVERTENCIA: No se encontró el entorno virtual en cPanel.")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')

import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser 'admin' created with password 'admin'")
else:
    print("Superuser 'admin' already exists")
