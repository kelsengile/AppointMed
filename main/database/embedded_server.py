"""
Launches a bundled, portable MySQL server as a background process so the
"server" device never needs a manual MySQL install or Workbench.

Setup (one-time, done by you before building/distributing the app):
1. Download the MySQL "ZIP Archive" (not the .msi installer) from
   https://dev.mysql.com/downloads/mysql
2. Extract it into: resources/mysql/  (so resources/mysql/bin/mysqld.exe exists)

From then on, whichever device runs the app with EMBEDDED_SERVER_ENABLED=True
in config/settings.py will silently start its own private MySQL instance on
first launch, using a local data folder next to the app — no installer, no
Workbench, nothing for the user to configure.

Client devices (Doctor/Nurse laptops) should leave EMBEDDED_SERVER_ENABLED
as False — they only ever connect over the network to the server device's IP,
exactly as before.
"""

import os
import subprocess
import time
import atexit
import mysql.connector
from mysql.connector import Error as MySQLError

from config.settings import DB_CONFIG

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MYSQL_DIR = os.path.join(BASE_DIR, "resources", "mysql")
MYSQLD_PATH = os.path.join(MYSQL_DIR, "bin", "mysqld.exe")
DATA_DIR = os.path.join(BASE_DIR, "resources", "mysql_data")
PORT = DB_CONFIG.get("port", 3306)
ROOT_PASSWORD = DB_CONFIG.get("password", "changeme")

_process = None  # holds the running mysqld subprocess, module-level singleton


def _is_first_run() -> bool:
    """The data directory only exists after MySQL has been initialized once."""
    return not os.path.isdir(DATA_DIR) or not os.listdir(DATA_DIR)


def _initialize_data_dir():
    """Creates MySQL's internal system tables and sets the root password.
    Only runs once, the very first time the app starts on this device."""
    os.makedirs(DATA_DIR, exist_ok=True)

    subprocess.run([
        MYSQLD_PATH,
        f"--datadir={DATA_DIR}",
        f"--basedir={MYSQL_DIR}",
        "--initialize-insecure",  # creates root user with NO password initially
    ], check=True)

    # Start it briefly, unprotected, just long enough to set the real password
    temp_proc = subprocess.Popen([
        MYSQLD_PATH,
        f"--datadir={DATA_DIR}",
        f"--basedir={MYSQL_DIR}",
        f"--port={PORT}",
        "--bind-address=127.0.0.1",
    ])
    _wait_until_ready(host="127.0.0.1", timeout=20)

    conn = mysql.connector.connect(host="127.0.0.1", port=PORT, user="root", password="")
    cursor = conn.cursor()
    cursor.execute(f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{ROOT_PASSWORD}';")
    cursor.execute("FLUSH PRIVILEGES;")
    conn.commit()
    cursor.close()
    conn.close()

    temp_proc.terminate()
    temp_proc.wait()


def _wait_until_ready(host="127.0.0.1", timeout=20):
    """Polls until MySQL accepts connections, or gives up after `timeout` seconds."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = mysql.connector.connect(host=host, port=PORT, user="root", password="")
            conn.close()
            return
        except MySQLError:
            try:
                conn = mysql.connector.connect(host=host, port=PORT, user="root",
                                                password=ROOT_PASSWORD)
                conn.close()
                return
            except MySQLError:
                time.sleep(0.5)
    raise TimeoutError("MySQL did not become ready in time.")


def start():
    """Starts the embedded MySQL server, initializing it first if this is
    the first time it's ever been run on this device. Safe to call once,
    early in main.py, before opening any windows."""
    global _process

    if not os.path.exists(MYSQLD_PATH):
        raise FileNotFoundError(
            "Bundled MySQL not found. Download the MySQL ZIP archive from "
            "dev.mysql.com/downloads/mysql and extract it into resources/mysql/ "
            "so that resources/mysql/bin/mysqld.exe exists."
        )

    if _is_first_run():
        _initialize_data_dir()

    _process = subprocess.Popen([
        MYSQLD_PATH,
        f"--datadir={DATA_DIR}",
        f"--basedir={MYSQL_DIR}",
        f"--port={PORT}",
        "--bind-address=0.0.0.0",  # 0.0.0.0 = reachable from other devices on the network
    ])

    _wait_until_ready(host="127.0.0.1")
    atexit.register(stop)


def stop():
    """Shuts down the embedded server cleanly when the app exits."""
    global _process
    if _process is not None:
        _process.terminate()
        _process.wait()
        _process = None
