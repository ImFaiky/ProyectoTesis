import os
import sys

# Agregar la ruta del proyecto al PATH de Python para que Passenger encuentre los módulos
sys.path.insert(0, os.path.dirname(__file__))

# Configurar el módulo de configuración por defecto de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')

# Importar el WSGI application de Django para que Passenger lo llame
from gamification_project.wsgi import application
