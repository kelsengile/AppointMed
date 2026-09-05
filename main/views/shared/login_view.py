"""
Login window — CustomTkinter version.
Same logic/controller as before, just modern widgets instead of plain ttk.
"""

import customtkinter as ctk

from controllers.auth_controller import AuthController
from utils.exceptions import AppointMedError
from models.user import Doctor, Nurse, Admin

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class LoginView(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AppointMed — Login")
        self.geometry("400x480")
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

        self.status_label = ctk.CTkLabel(card, text="", text_color="#d64545")
        self.status_label.pack(pady=(16, 0))

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


if __name__ == "__main__":
    LoginView().mainloop()
