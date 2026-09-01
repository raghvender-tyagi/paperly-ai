"""
WSGI config for paperlydjango project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paperlydjango.settings')

application = get_wsgi_application()

# Run database migrations automatically on startup
try:
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"Startup migration warning: {e}")

