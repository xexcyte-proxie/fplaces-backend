from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

ENV_MODE = env("ENV_MODE", default="local")  # Options: local, dev, prod

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")

DEBUG = env.bool("DEBUG", default=(ENV_MODE in ["local", "dev"]))

ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

INSTALLED_APPS = [
    "daphne",
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "core",
    "users",
    "forum",
    "notifications",
    "payments",
    "map",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.LogRequest",
    "core.middleware.UpdateLastLoginMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# channels-redis fans events out across multiple processes/workers; with no REDIS_URL
# set (plain local dev), an in-memory layer is used instead (single process only).
REDIS_URL = env("REDIS_URL", default=None)
CHANNEL_LAYERS = {
    "default": (
        {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
        if REDIS_URL
        else {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    )
}


# Database
# Postgres is used whenever DATABASE_URL is set, or if we are in local/dev mode and individual DB_* variables are provided.
# Falls back to SQLite for plain local development.
if env("DATABASE_URL", default=None):
    DATABASES = {
        "default": env.db("DATABASE_URL")
    }
elif ENV_MODE in ["local", "dev"] and env("DB_HOST", default=None):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="postgres"),
            "USER": env("DB_USER", default=""),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default=""),
            "PORT": env.int("DB_PORT", default=5432),
        }
    }
else:
    DATABASES = {
        "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    }


AUTH_USER_MODEL = "users.User"

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
STATIC_ROOT = BASE_DIR / "staticfiles" / "static"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "fplaces API",
    "DESCRIPTION": (
        "Real-time, venue-based social platform API.\n\n"
        "Fans inside the same stadium/venue share a live feed tied to physical sections: "
        "posts, comments, upvotes, and flags, plus live crowd-sourced section heatmaps.\n\n"
        "## Authentication\n"
        "Most endpoints require a JWT access token. Obtain one via `POST /api/users/login/`, "
        "then send it as `Authorization: Bearer <access_token>`. Access tokens expire after "
        "30 minutes; use `POST /api/users/token/refresh/` with the refresh token to renew.\n\n"
        "WebSocket connections (venue rooms, personal notifications) authenticate via a "
        "`?token=<access_token>` query parameter instead of a header.\n\n"
        "## Error format\n"
        "All error responses (validation, auth, permission, not-found, server errors) share a "
        "single envelope:\n\n"
        "```json\n"
        "{\n"
        '  "status": "error",\n'
        '  "message": "Human-readable summary",\n'
        '  "details": { "field": ["..."] }\n'
        "}\n"
        "```\n\n"
        "## Soft delete\n"
        "Nothing is hard-deleted. `DELETE` on any resource archives it (`is_archived=True`) "
        "instead of removing the row; archived records are excluded from normal querysets. "
        "Most resources expose a `POST /{id}/restore/` action to bring them back.\n\n"
        '<br/><a href="/api/guide.html" target="_blank" style="display:inline-block; padding:10px 20px; background-color:#00e096; color:#08090c; text-decoration:none; border-radius:8px; font-weight:bold;">📖 View Frontend Integration Guide</a>'
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "TAGS": [
        {"name": "Auth", "description": "Registration, login/refresh, email verification, password reset."},
        {"name": "Users", "description": "Authenticated user's own profile."},
        {"name": "Categories", "description": "Fixed set of post categories (Lines and Crowds, Food and Drinks, Fan Vibe, Help)."},
        {"name": "Venues", "description": "Stadiums/arenas fans can select to join a live feed."},
        {"name": "Sections", "description": "Physical zones within a venue (e.g. North Stand, VIP), used for the section heatmap."},
        {"name": "Posts", "description": "140-character venue feed posts, with upvotes, flags, and moderation."},
        {"name": "Comments", "description": "Threaded replies on posts."},
        {"name": "Notifications", "description": "Per-user notification inbox, also pushed live over WebSocket."},
        {"name": "Admin", "description": "Administrative metrics, moderation controls, and user management."},
    ],
    "CONTACT": {"name": "fplaces", "email": "support@fplaces.app"},
    "LICENSE": {"name": "Proprietary"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}


PROJECT_NAME = "fplaces"
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# All outbound mail is sent through notifications.services.mail, which calls the
# Resend API. With no key set (e.g. local dev), it logs the email instead of sending.
RESEND_API_KEY = env("RESEND_API_KEY", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@fplaces.app")

MAPPEDIN_KEY = env("MAPPEDIN_KEY", default="")
MAPPEDIN_SECRET = env("MAPPEDIN_SECRET", default="")
