"""
AppointMed — entry point.
Run this file on every client device; each one connects to the same
central database (see config/settings.py) so all users stay in sync.

On startup, this automatically applies database/schema.sql if the
database/tables don't exist yet — no manual MySQL Workbench step needed.
The one thing that IS still required on the server device: MySQL Server
itself must be installed and running (see README.md).
"""

import tkinter as tk
from tkinter import messagebox

from database.initializer import ensure_database_ready
from utils.exceptions import AppointMedError

if __name__ == "__main__":
    try:
        ensure_database_ready()
    except AppointMedError as e:
        # Show a plain error dialog instead of crashing with a traceback,
        # since at this point no other window exists yet.
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database setup failed", str(e))
        raise SystemExit(1)

    from views.shared.login_view import LoginView
    app = LoginView()
    app.mainloop()
