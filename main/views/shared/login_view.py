"""
Login window — CustomTkinter version.

Works even with no database connection: the window always opens. If the
app can't reach a database, logging in will just show a clear error
instead of crashing, and the user can use "Connect to Server" to point
the app at a different host without editing any files.
"""

import customtkinter as ctk

from config import settings
from controllers.auth_controller import AuthController
from database.initializer import ensure_database_ready
from utils.exceptions import AppointMedError
from models.user import Doctor, Nurse, Admin

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class LoginView(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AppointMed — Login")
        self.geometry("400x520")
        self.resizable(False, False)
        self.auth_controller = AuthController()
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, corner_radius=16)
        card.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            card, text="AppointMed",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(36, 4))

        ctk.CTkLabel(
            card, text="Clinic Appointment System",
            font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(pady=(0, 32))

        self.username_entry = ctk.CTkEntry(
            card, placeholder_text="Username", width=260, height=40
        )
        self.username_entry.pack(pady=(0, 14))

        self.password_entry = ctk.CTkEntry(
            card, placeholder_text="Password", show="*", width=260, height=40
        )
        self.password_entry.pack(pady=(0, 28))
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        ctk.CTkButton(
            card, text="Log in", width=260, height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_login
        ).pack()

        self.status_label = ctk.CTkLabel(card, text="", text_color="#d64545", wraplength=260)
        self.status_label.pack(pady=(16, 0))

        # "Connect to Server" — lets the user (re)point the app at a
        # database without editing config/settings.py by hand.
        ctk.CTkButton(
            card, text="Connect to Server", width=260, height=32,
            fg_color="transparent", border_width=1, border_color="gray70",
            text_color="gray30", hover_color="gray90",
            command=self._open_connect_modal
        ).pack(pady=(20, 0))

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        try:
            user = self.auth_controller.login(username, password)
        except AppointMedError as e:
            self.status_label.configure(text=str(e))
            return

        self.destroy()
        self._open_dashboard(user)

    def _open_dashboard(self, user):
        if isinstance(user, Doctor):
            from views.doctor.doctor_dashboard import DoctorDashboard
            DoctorDashboard(user).mainloop()
        elif isinstance(user, Nurse):
            from views.nurse.nurse_dashboard import NurseDashboard
            NurseDashboard(user).mainloop()
        elif isinstance(user, Admin):
            from views.admin.admin_dashboard import AdminDashboard
            AdminDashboard(user).mainloop()

    # ---------- Connect to Server modal ----------

    def _open_connect_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Connect to Server")
        modal.geometry("360x420")
        modal.resizable(False, False)
        modal.grab_set()  # modal: blocks interaction with the login window

        ctk.CTkLabel(
            modal, text="Connect to Server",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(24, 4))
        ctk.CTkLabel(
            modal, text="Point AppointMed at your clinic's database server.",
            font=ctk.CTkFont(size=12), text_color="gray50", wraplength=280
        ).pack(pady=(0, 20))

        host_entry = self._labeled_entry(modal, "Server address (IP)", settings.DB_CONFIG["host"])
        username_entry = self._labeled_entry(modal, "Username", settings.DB_CONFIG["user"])
        password_entry = self._labeled_entry(modal, "Password", "", show="*")

        status_label = ctk.CTkLabel(modal, text="", text_color="#d64545", wraplength=280)
        status_label.pack(pady=(10, 0))

        def connect():
            host = host_entry.get().strip()
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not host or not username:
                status_label.configure(text="Server address and username are required.")
                return

            # Try the new settings before committing to them, so a bad
            # entry doesn't leave the app pointed at a broken config.
            previous = dict(settings.DB_CONFIG)
            settings.DB_CONFIG["host"] = host
            settings.DB_CONFIG["user"] = username
            settings.DB_CONFIG["password"] = password

            status_label.configure(text_color="gray40", text="Connecting...")
            modal.update_idletasks()

            try:
                ensure_database_ready()
            except AppointMedError as e:
                settings.DB_CONFIG.update(previous)  # roll back on failure
                status_label.configure(text_color="#d64545", text=str(e))
                return

            status_label.configure(text_color="#2F855A", text="Connected successfully.")
            modal.after(700, modal.destroy)

        ctk.CTkButton(modal, text="Connect", command=connect).pack(pady=24)

    def _labeled_entry(self, parent, label_text, default_value="", show=None):
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(fill="x", padx=30, pady=(6, 2))
        entry = ctk.CTkEntry(parent, width=300, show=show) if show else ctk.CTkEntry(parent, width=300)
        if default_value:
            entry.insert(0, default_value)
        entry.pack(padx=30)
        return entry


if __name__ == "__main__":
    LoginView().mainloop()
