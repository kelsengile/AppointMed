"""
Nurse/Secretary dashboard — scoped to the ONE doctor they are assigned to
(nurse.assigned_doctor_id). Lets them add/edit/cancel appointments on
that doctor's behalf.
"""

import tkinter as tk
from tkinter import ttk

from controllers.appointment_controller import AppointmentController


class NurseDashboard(tk.Tk):
    def __init__(self, nurse):
        super().__init__()
        self.nurse = nurse
        self.appointment_controller = AppointmentController()

        self.title(nurse.dashboard_title())
        self.geometry("1100x700")
        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(
            self,
            text=f"{self.nurse.dashboard_title()} — managing Dr. #{self.nurse.assigned_doctor_id}",
            font=("Segoe UI", 16, "bold"),
        )
        header.pack(anchor="w", padx=20, pady=16)

        # TODO: appointment list for self.nurse.assigned_doctor_id
        # TODO: add/edit/delete appointment forms
        placeholder = ttk.Label(self, text="Assigned doctor's schedule goes here.")
        placeholder.pack(padx=20)
