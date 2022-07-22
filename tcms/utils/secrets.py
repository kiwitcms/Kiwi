"""
Helper module which deals with loading values from ENV or Docker Secrets.
"""
import os


def get_secret(key, default):
    """
    key could be:
        - an ENV variable
        - /run/secrets/a_secret_name
        - /arbitrary/file/inside/container
    """
    value = os.environ.get(key, default)

    if value and value.startswith("/") and os.path.isfile(value):
        with open(value, "r", encoding="utf-8") as secret_file:
            return secret_file.read().strip()

    return value
