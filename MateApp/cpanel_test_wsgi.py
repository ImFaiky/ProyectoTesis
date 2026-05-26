import os
import sys

# 1. Activar el entorno virtual
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
    print("ERROR: No se encontró el entorno virtual.")
    sys.exit(1)

print("==================================================")
print("     PRUEBA DE ARRANQUE WSGI (PASSENGER)")
print("==================================================")

# 2. Cambiar al directorio de la app e intentar importar passenger_wsgi
try:
    app_path = '/home/damisoft/mate-ia.damisoft-ec.com/MateApp'
    os.chdir(app_path)
    sys.path.insert(0, app_path)
    
    print("Intentando importar passenger_wsgi...")
    import passenger_wsgi
    print("\n>>> ¡WSGI importado con éxito! El servidor Passenger puede iniciar la app. <<<")
    print(f"Objeto WSGI detectado: {passenger_wsgi.application}")
except Exception as e:
    print("\n!!! ERROR CRÍTICO EN EL ARRANQUE WSGI !!!")
    import traceback
    traceback.print_exc()

print("==================================================")
