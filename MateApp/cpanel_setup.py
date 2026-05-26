import os
import sys

# =========================================================================
# ACTIVACIÓN DINÁMICA DEL ENTORNO VIRTUAL EN CPANEL
# =========================================================================
# cPanel a veces ejecuta scripts con el Python global en lugar de usar el virtualenv.
# Este bloque busca y activa automáticamente tu entorno virtual de producción.
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
    print("ADVERTENCIA: No se encontró el entorno virtual en cPanel. Usando Python por defecto.")

# Agregar el directorio raíz de Django al PATH
sys.path.insert(0, os.path.dirname(__file__))

import django

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
