"""
Minimal Django settings for Connection_Type project.
Configured for local development with SQLite by default, and optional DATABASE_URL.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-connection-type-key")
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")
# Always provide a safe fallback for local/dev even if DEBUG=False
_hosts_env = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h]
ALLOWED_HOSTS = _hosts_env or ["127.0.0.1", "localhost", "0.0.0.0"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "connection_ai.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "connection_ai.wsgi.application"
ASGI_APPLICATION = "connection_ai.asgi.application"

# Database: default to SQLite for local dev; override with DATABASE_URL if set
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.parse(os.getenv("DATABASE_URL"))

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework: JSON-only in production, Browsable API in debug
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ) if not DEBUG else (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
    ),
}

# Logging: basic structured logs suitable for production
LOGGING = {
    "version": 1,
    # Allow default Django dev server request logging to show status lines
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        # Suppress Django dev server request logs
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",  # show "GET ... 200" status lines as usual
            "propagate": False,
        },
        # Quiet noisy third-party libs
        "httpx": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "google_genai": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "google_genai.models": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "langchain": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "urllib3": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "google.auth": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        # App logger to show concise API status lines
        "api": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Suppress specific runtime warnings in dev related to naive datetimes
try:
    import warnings
    warnings.filterwarnings(
        "ignore",
        message="DateTimeField .* received a naive datetime.*",
        category=RuntimeWarning,
    )
except Exception:
    pass

# Security hardening toggled by DEBUG
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Default to False for local dev; explicitly enable in production via env
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() in ("1", "true", "yes")
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False