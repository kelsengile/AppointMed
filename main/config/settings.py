"""
Central configuration for AppointMed.
This is just a plain Python file with settings the rest of the app reads
from. In a real app, secrets like passwords should not be hardcoded here,
but for this class project it keeps things simple.
"""

DB_CONFIG = {
    "host": "",       # put your MySQL server's IP address here
    "port": 3306,
    "user": "",
    "password": "",
    "database": "appointmed_db",
}

APP_NAME = "AppointMed"
APP_VERSION = "0.1.0"

# UI defaults
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
THEME_COLOR = "#2E86AB"
