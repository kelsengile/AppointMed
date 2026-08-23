"""
Admin dashboard — CustomTkinter version.
Full visibility: lists all Doctor/Nurse/Admin accounts and lets the
admin add new ones, including assigning a nurse to a doctor.
"""

import customtkinter as ctk
from tkinter import messagebox

from controllers.user_controller import UserController
from utils.exceptions import AppointMedError

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

ROLE_COLORS = {
    "doctor": ("#E3F0FF", "#2B6CB0"),
    "nurse": ("#F3E8FF", "#6B46C1"),
    "admin": ("#FBE7E7", "#C53030"),
}

SAMPLE_USERS = [
    {"id": 1, "full_name": "Juan Diaz", "username": "drdiaz", "role": "doctor", "specialization": "Pediatrics", "assigned_doctor_id": None},
    {"id": 2, "full_name": "Jane Santos", "username": "nursejane", "role": "nurse", "specialization": None, "assigned_doctor_id": 1},
    {"id": 3, "full_name": "System Administrator", "username": "admin", "role": "admin", "specialization": None, "assigned_doctor_id": None},
]


class AdminDashboard(ctk.CTk):
    def __init__(self, admin):
        super().__init__()
        self.admin = admin
        self.user_controller = UserController()

        self.title(admin.dashboard_title())
        self.geometry("980x680")
        self._build_ui()
        self._load_users()

    # ---------- layout ----------

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text=self.admin.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Add user", width=120, command=self._open_add_form
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color="gray60",
            command=self._load_users
        ).pack(side="right")

        ctk.CTkLabel(
            self, text="User accounts", font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def _clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    # ---------- data ----------

    def _load_users(self):
        self._clear_list()
        try:
            users = self.user_controller.get_all_users()
        except AppointMedError:
            users = SAMPLE_USERS

        if not users:
            ctk.CTkLabel(self.list_frame, text="No users found.", text_color="gray50").pack(pady=40)
            return

        for user in users:
            self._add_user_row(user)

    # ---------- user rows ----------

    def _add_user_row(self, user):
        row = ctk.CTkFrame(self.list_frame, corner_radius=10)
        row.pack(fill="x", pady=5)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        ctk.CTkLabel(
            info, text=user["full_name"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")

        subtitle = f"@{user['username']}"
        if user["role"] == "doctor" and user.get("specialization"):
            subtitle += f" · {user['specialization']}"
        if user["role"] == "nurse" and user.get("assigned_doctor_id"):
            subtitle += f" · assigned to doctor #{user['assigned_doctor_id']}"
        ctk.CTkLabel(
            info, text=subtitle, font=ctk.CTkFont(size=12), text_color="gray50", anchor="w"
        ).pack(fill="x")

        bg, fg = ROLE_COLORS.get(user["role"], ROLE_COLORS["admin"])
        ctk.CTkLabel(
            row, text=user["role"].capitalize(), fg_color=bg, text_color=fg,
            corner_radius=8, width=80, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        ctk.CTkButton(
            row, text="Delete", width=70, height=26,
            fg_color="#C53030", hover_color="#9B2C2C",
            command=lambda u=user: self._delete_user(u)
        ).pack(side="right", padx=(8, 0))

    def _delete_user(self, user):
        if not messagebox.askyesno("Confirm", f"Delete account for {user['full_name']}?"):
            return
        try:
            self.user_controller.delete_user(user["id"])
        except AppointMedError as e:
            messagebox.showerror("Error", str(e))
        self._load_users()

    # ---------- add user form ----------

    def _open_add_form(self):
        form = ctk.CTkToplevel(self)
        form.title("Add User")
        form.geometry("380x560")
        form.grab_set()

        ctk.CTkLabel(
            form, text="New User Account", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 16))

        username_entry = self._labeled_entry(form, "Username")
        password_entry = self._labeled_entry(form, "Password", show="*")
        full_name_entry = self._labeled_entry(form, "Full name")

        ctk.CTkLabel(form, text="Role", anchor="w").pack(fill="x", padx=30, pady=(10, 2))
        role_var = ctk.StringVar(value="doctor")
        role_menu = ctk.CTkOptionMenu(form, values=["doctor", "nurse", "admin"], variable=role_var)
        role_menu.pack(padx=30, fill="x")

        specialization_entry = self._labeled_entry(form, "Specialization (doctors only)")
        doctor_id_entry = self._labeled_entry(form, "Assigned doctor ID (nurses only)")

        status_label = ctk.CTkLabel(form, text="", text_color="#d64545")
        status_label.pack(pady=(4, 0))

        def submit():
            try:
                role = role_var.get()
                self.user_controller.add_user(
                    username=username_entry.get().strip(),
                    password=password_entry.get().strip(),
                    full_name=full_name_entry.get().strip(),
                    role=role,
                    specialization=specialization_entry.get().strip() or None if role == "doctor" else None,
                    assigned_doctor_id=int(doctor_id_entry.get()) if role == "nurse" and doctor_id_entry.get().strip() else None,
                )
                form.destroy()
                self._load_users()
            except AppointMedError as e:
                status_label.configure(text=str(e))
            except ValueError:
                status_label.configure(text="Assigned doctor ID must be a number.")

        ctk.CTkButton(form, text="Create account", command=submit).pack(pady=24)

    def _labeled_entry(self, parent, label_text, show=None):
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(fill="x", padx=30, pady=(10, 2))
        entry = ctk.CTkEntry(parent, width=300, show=show) if show else ctk.CTkEntry(parent, width=300)
        entry.pack(padx=30)
        return entry
