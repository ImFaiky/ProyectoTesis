"""
WSGI config for gamification_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import pymysql

pymysql.install_as_MySQLdb()
if hasattr(pymysql, 'version_info'):
    pymysql.version_info = (2, 2, 4, "final", 0)
    
if not hasattr(pymysql.connections.Connection, 'cursor_factory'):
    pymysql.connections.Connection.cursor_factory = None

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamification_project.settings')

application = get_wsgi_application()
