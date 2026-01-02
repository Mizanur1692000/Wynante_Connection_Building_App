"""
WSGI config for Connection_Type project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "connection_ai.settings")

application = get_wsgi_application()
