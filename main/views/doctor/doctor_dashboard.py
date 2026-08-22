"""
Doctor's own dashboard window — shows their schedule for the day and
patient history. Fill in the Treeview + calendar widget here.
"""

import tkinter as tk
from tkinter import ttk

from controllers.appointment_controller import AppointmentController


class DoctorDashboard(tk.Tk):
    def __init__(self, doctor):
        super().__init__()
        self.doctor = doctor
        self.appointment_controller = AppointmentController()

        self.title(doctor.dashboard_title())
        self.geometry("1100x700")
        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(self, text=self.doctor.dashboard_title(),
                            font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", padx=20, pady=16)

        # TODO: ttk.Treeview listing today's appointments
        # TODO: buttons for view patient history / mark completed / cancel
        placeholder = ttk.Label(self, text="Appointment schedule goes here.")
        placeholder.pack(padx=20)
