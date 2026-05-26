import os
import sys
import django

# Agregar el directorio raíz del proyecto al PATH para que Django pueda cargar los módulos
sys.path.insert(0, os.path.dirname(__file__))

# Configurar las variables de entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')

# Inicializar Django
django.setup()

from django.core.management import call_command

print("==================================================")
print("   INICIANDO CONFIGURACIÓN DE MATEAPP EN CPANEL")
print("==================================================")

# 1. Ejecutar las migraciones de Base de Datos
try:
    print("\n[1/2] Ejecutando migraciones de Base de Datos...")
    call_command('migrate', interactive=False)
    print(">>> ¡Migraciones completadas con éxito! <<<")
except Exception as e:
    print(f"!!! Error al ejecutar migraciones: {e} !!!")
    import traceback
    traceback.print_exc()

# 2. Recolectar los archivos estáticos
try:
    print("\n[2/2] Recolectando archivos estáticos (collectstatic)...")
    call_command('collectstatic', interactive=False)
    print(">>> ¡Archivos estáticos recopilados con éxito! <<<")
except Exception as e:
    print(f"!!! Error al recopilar archivos estáticos: {e} !!!")
    import traceback
    traceback.print_exc()

print("\n==================================================")
print("         PROCESO DE CONFIGURACIÓN TERMINADO")
print("==================================================")
