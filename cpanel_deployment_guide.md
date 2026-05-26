# Guía Oficial de Despliegue en cPanel sin Consola (MateApp)

Esta guía detalla el flujo de trabajo optimizado para subir cambios a producción, realizar migraciones, recopilar archivos estáticos y reiniciar tu servidor de forma **100% visual y automatizada**, sin necesidad de abrir una consola de comandos (SSH) en tu cPanel.

---

## 🛠️ Estructura del Servidor en Producción

El repositorio está clonado en la siguiente ruta absoluta de cPanel:
* `/home/damisoft/mate-ia.damisoft-ec.com` (Raíz del repositorio Git)
  * `MateApp/` (Carpeta del proyecto Django)
    * `cpanel_setup.py` *(El automatizador todo-en-uno)*
    * `cpanel_pip_debug.py` *(El depurador de dependencias)*
    * `create_superuser.py` *(El creador del administrador)*
    * `requirements.txt` *(Lista de dependencias)*
    * `.env` *(Variables de entorno y base de datos)*

---

## 🚀 Flujo Diario de Despliegue (En 3 Pasos)

Cada vez que realices cambios locales en tu computadora y quieras subirlos al servidor, sigue este flujo:

### Paso 1: Sube tus cambios a GitHub (Desde tu PC)
Abre la consola en tu computadora local dentro del proyecto y ejecuta:
```bash
git add .
git commit -m "Descripción de tus cambios"
git push origin main
```

### Paso 2: Descarga los cambios a cPanel (Visual)
1. Inicia sesión en tu **cPanel**.
2. Abre la herramienta **Git™ Version Control** (Control de Versiones Git).
3. Haz clic en el botón **Manage** (Gestionar) al lado de tu repositorio `mate-ia`.
4. Ve a la pestaña **Pull or Deploy** (Obtener o desplegar).
5. Haz clic en el botón azul **Update from Remote** (esto descargará tu último código de GitHub en segundos).

### Paso 3: Aplica los cambios, publica estáticos y reinicia (Visual)
1. Ve a **Setup Python App** (Configurar aplicación Python) en cPanel.
2. Haz clic en el lápiz para **Editar** tu aplicación `mate-ia.damisoft-ec.com/MateApp`.
3. Baja hasta la sección **Execute python script** (Ejecutar script de Python).
4. Escribe exactamente:
   ```text
   MateApp/cpanel_setup.py
   ```
5. Haz clic en el botón **Run** (Ejecutar).

---

## ⚡ Guía de Scripts Especiales (Tus Herramientas)

Hemos implementado tres scripts de ayuda en la carpeta `MateApp` para realizar operaciones complejas desde la interfaz visual de cPanel:

### 1. `MateApp/cpanel_setup.py` (El Automatizador Todo-En-Uno)
Ejecútalo cada vez que descargues una actualización de Git. Realiza secuencialmente:
1. **Migraciones:** Corre `migrate` de Django para actualizar las tablas en MySQL de producción.
2. **Compilación de Estáticos:** Agrupa los CSS/JS en la carpeta interna `static_collected/`.
3. **Publicación en la Web:** Copia recursivamente los archivos estáticos a la carpeta pública del subdominio `/home/damisoft/mate-ia.damisoft-ec.com/static`.
4. **Reinicio de Web:** Toca `tmp/restart.txt` para forzar a Passenger a reiniciar tu web de inmediato.

### 2. `MateApp/cpanel_pip_debug.py` (Depurador de Dependencias)
Ejecútalo si agregas un nuevo paquete a tu `requirements.txt` y necesitas instalarlo en el servidor:
* Corre `pip install` dentro de tu entorno virtual de Python 3.11 capturando todo el historial de instalación en pantalla.

### 3. `MateApp/create_superuser.py` (Creador del Administrador)
Ejecútalo si necesitas crear o recuperar el superusuario del panel de administración (`/admin/`):
* Crea un usuario administrador con los valores que tenga configurados (por defecto: usuario `admin`, clave `admin`). Puedes editar estas credenciales abriendo el archivo en el Administrador de Archivos antes de ejecutarlo.

---

## ⚠️ Consejos Importantes y Solución de Problemas

* **¿Cómo editar credenciales de Base de Datos en producción?**
  El archivo `.env` vive en la subcarpeta `MateApp/` de tu servidor. Si cambias de base de datos o de clave de Gemini AI, edítalo usando el Administrador de Archivos de cPanel.
* **El botón "Deploy Head" de Git en cPanel está bloqueado:**
  ¡No te preocupes! cPanel deshabilita este botón con facilidad si detecta cambios temporales. **No lo necesitas**. El script `cpanel_setup.py` hace exactamente lo mismo (copiado de estáticos y reinicio) de forma mucho más confiable.
* **¿Qué versión de Python debo usar?**
  Mantén configurada la versión **Python 3.11** en cPanel Setup Python App, ya que es compatible con Django 5.1/5.2. (Django 6.0 requiere Python 3.12, que no está disponible en tu hosting).
