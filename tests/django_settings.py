DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    },
    "other": {
        "ENGINE": "django.db.backends.sqlite3",
    },
}

SECRET_KEY = "django_tests_secret_key"

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

USE_TZ = False

ROOT_URLCONF = "tests.django_urls"
