import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-do-not-deploy")
if os.getenv("DJANGO_SECRET_KEY_FILE"):
    SECRET_KEY = Path(os.environ["DJANGO_SECRET_KEY_FILE"]).read_text().strip()
if not DEBUG and SECRET_KEY == "local-development-only-do-not-deploy":
    raise RuntimeError("Set DJANGO_SECRET_KEY before enabling production mode.")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,api").split(
    ","
)
ROOT_URLCONF = "coach.urls"
WSGI_APPLICATION = "coach.wsgi.application"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DATABASE_PATH", str(BASE_DIR / "local.sqlite3")),
    }
}
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200,http://localhost:8080,http://127.0.0.1:8080",
).split(",")
SECURE_CONTENT_TYPE_NOSNIFF = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Local singleton only. Shared rate limits are required before multi-replica hosting.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "practice-local",
        "OPTIONS": {"MAX_ENTRIES": 2000},
    }
}

# Only the loopback reverse proxy may supply the production scheme and client address.
TRUST_LOCAL_PROXY = os.getenv("TRUST_LOCAL_PROXY", "false").lower() == "true"
if TRUST_LOCAL_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
