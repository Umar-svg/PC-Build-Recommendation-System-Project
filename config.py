# config.py — Database and Flask configuration
#
# This file reads settings from environment variables first.
# If a variable isn't set (i.e. running on your laptop), it falls back to
# the local default. This means:
#   - On your laptop: connects to local MySQL with your local password.
#   - On Railway: Railway injects MYSQLHOST, MYSQLPASSWORD, etc. automatically,
#     so the env vars take over and the app connects to Railway's MySQL.
# No code change is needed when switching between local and deployed.

import os


class Config:
    # MySQL settings — environment variables (Railway) override local defaults.
    MYSQL_HOST     = os.environ.get("MYSQLHOST", "localhost")
    MYSQL_USER     = os.environ.get("MYSQLUSER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD", "Umar@1")
    MYSQL_DB       = os.environ.get("MYSQLDATABASE", "pc_build_db")
    MYSQL_PORT     = int(os.environ.get("MYSQLPORT", 3306))

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-to-a-long-random-string")
    DEBUG      = os.environ.get("FLASK_DEBUG", "1") == "1"
