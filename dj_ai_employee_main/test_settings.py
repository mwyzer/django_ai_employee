"""Test settings — uses in-memory SQLite instead of MySQL."""
from .settings import *

# Override database to use SQLite in-memory for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable DEBUG for cleaner test output
DEBUG = False

# Fake API key for tests — never hit real DeepSeek
DEEPSEEK_API_KEY = 'sk-test-fake-key'
DEEPSEEK_MODEL = 'deepseek-chat'
