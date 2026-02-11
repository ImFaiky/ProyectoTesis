# Proyecto Gamificación Tesis

Plataforma de gamificación para el aprendizaje de matemáticas, desarrollada con Django y MySQL.

## Requisitos Previos

- Python 3.10+
- MySQL Server
- Git

## Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <url-del-repositorio>
    cd MateApp
    ```

2.  **Crear y activar entorno virtual:**

    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install django djangorestframework django-cors-headers pymysql python-dotenv
    # O si existe requirements.txt:
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno:**

    - Copia el archivo de ejemplo:
      ```bash
      cp .env.example .env
      ```
    - Edita `.env` con tus credenciales de base de datos:
      ```ini
      DB_NAME=nombre_base_datos
      DB_USER=usuario
      DB_PASSWORD=contraseña
      DB_HOST=127.0.0.1
      DB_PORT=3306
      ```

5.  **Base de Datos:**

    - Crea la base de datos en tu servidor MySQL (ej. `create database mateapp;`).
    - Ejecuta las migraciones:
      ```bash
      python manage.py migrate
      ```

6.  **Crear Superusuario:**

    ```bash
    python manage.py createsuperuser
    ```

## Ejecución

Inicia el servidor de desarrollo:

```bash
python manage.py runserver
```

Accede a:
- Web: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Roles de Usuario

El sistema maneja dos tipos de permisos principales:

- **Admin/Profesor (Staff/Superuser)**: Acceso total al panel de administración para gestionar estudiantes, niveles y disciplinas.
- **Estudiante**: Acceso restringido al dashboard de usuario y juegos.
