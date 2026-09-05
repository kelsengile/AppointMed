"""
Central configuration for AppointMed.
Keep secrets out of source control in a real deployment (use a .env file
+ python-dotenv instead of hardcoding). This file is a placeholder so the
app has one obvious place to read connection info from.
"""

DB_CONFIG = {
    "host": "localhost",       # replace with your central server's IP for multi-device access
    "port": 3306,
    "user": "root",
    "password": "password",
    "database": "appointmed_db",
}

APP_NAME = "AppointMed"
APP_VERSION = "0.1.0"

# UI defaults
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
THEME_COLOR = "#2E86AB"
