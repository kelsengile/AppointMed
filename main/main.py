"""
AppointMed — entry point.
Run this file on every client device; each one connects to the same
central database (see config/settings.py) so all users stay in sync.
"""

from views.shared.login_view import LoginView

if __name__ == "__main__":
    app = LoginView()
    app.mainloop()
