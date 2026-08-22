"""
Login window. On success, routes to the role-appropriate dashboard —
this is where polymorphism (dashboard_title/permissions) pays off.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from controllers.auth_controller import AuthController
from utils.exceptions import AppointMedError
from models.user import Doctor, Nurse, Admin


class LoginView(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AppointMed — Login")
        self.geometry("380x260")
        self.resizable(False, False)
        self.auth_controller = AuthController()
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=24)
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="AppointMed", font=("Segoe UI", 18, "bold")).pack(pady=(0, 16))

        ttk.Label(frame, text="Username").pack(anchor="w")
        self.username_entry = ttk.Entry(frame)
        self.username_entry.pack(fill="x", pady=(0, 12))

        ttk.Label(frame, text="Password").pack(anchor="w")
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.pack(fill="x", pady=(0, 20))

        ttk.Button(frame, text="Log in", command=self._handle_login).pack(fill="x")

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        try:
            user = self.auth_controller.login(username, password)
        except AppointMedError as e:
            messagebox.showerror("Login failed", str(e))
            return

        self.destroy()
        self._open_dashboard(user)

    def _open_dashboard(self, user):
        # Deferred imports avoid circular imports between view packages
        if isinstance(user, Doctor):
            from views.doctor.doctor_dashboard import DoctorDashboard
            DoctorDashboard(user).mainloop()
        elif isinstance(user, Nurse):
            from views.nurse.nurse_dashboard import NurseDashboard
            NurseDashboard(user).mainloop()
        elif isinstance(user, Admin):
            from views.admin.admin_dashboard import AdminDashboard
            AdminDashboard(user).mainloop()


if __name__ == "__main__":
    LoginView().mainloop()
