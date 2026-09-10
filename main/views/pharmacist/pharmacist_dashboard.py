



import customtkinter as ctk
from tkinter import messagebox
from datetime import date, datetime

from controllers.appointment_controller import AppointmentController
from utils.exceptions import AppointMedError

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

STATUS_COLORS = {
    "Scheduled": ("#EEF1F4", "#4A5568"),
    "Checked-in": ("#FFF6DC", "#B7791F"),
    "Completed": ("#E3F6E8", "#2F855A"),
    "Cancelled": ("#FBE7E7", "#C53030"),
}

class PharmacistDashboard(ctk.CTk):
    def __init__(self, pharmacist):
        super().__init__()
        self.pharmacist = pharmacist
        self.appointment_controller = AppointmentController()

        self.title(pharmacist.dashboard_title())
        self.geometry("900x680")
        self.build_ui()
        self.load_invoices()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text=self.pharmacist.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color="gray60",
            command=self.load_invoices
        ).pack(side="right")

        ctk.CTkLabel(
            self, text="Today — " + date.today().strftime("%A, %B %d"),
            font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def load_invoices(self):
        pass