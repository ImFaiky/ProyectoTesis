import os
import sys
import subprocess

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

# 2. Definir rutas
app_path = '/home/damisoft/mate-ia.damisoft-ec.com/MateApp'
req_path = os.path.join(app_path, 'requirements.txt')

print("==================================================")
print("      DEPURACIÓN DE PIP INSTALL EN CPANEL")
print("==================================================")
print(f"Ruta de requirements.txt: {req_path}\n")

# 3. Ejecutar pip install y capturar TODO el log de salida
try:
    # Usamos sys.executable para asegurarnos de que corra dentro del virtualenv activado
    cmd = f"{sys.executable} -m pip install -r {req_path}"
    print(f"Ejecutando: {cmd}\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    print("--- SALIDA ESTÁNDAR (STDOUT) ---")
    print(result.stdout if result.stdout else "(Sin salida)")
    
    print("\n--- SALIDA DE ERRORES (STDERR) ---")
    print(result.stderr if result.stderr else "(Sin errores)")
    
except Exception as e:
    print(f"Error al ejecutar pip: {e}")

print("==================================================")
