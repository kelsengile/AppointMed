"""
Admin dashboard — full visibility. Manage all user accounts
(doctors/nurses/admins) and view clinic-wide appointment data.
"""

import tkinter as tk
from tkinter import ttk


class AdminDashboard(tk.Tk):
    def __init__(self, admin):
        super().__init__()
        self.admin = admin

        self.title(admin.dashboard_title())
        self.geometry("1100x700")
        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(self, text=self.admin.dashboard_title(),
                            font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", padx=20, pady=16)

        # TODO: user management table (add/edit/delete doctor & nurse accounts,
        #       including assigning a nurse to a doctor)
        # TODO: clinic-wide appointment overview
        placeholder = ttk.Label(self, text="User management + clinic overview goes here.")
        placeholder.pack(padx=20)
