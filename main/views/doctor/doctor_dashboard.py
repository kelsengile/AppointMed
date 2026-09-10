"""
Doctor's dashboard — built with CustomTkinter.
Shows today's appointments as cards with a status badge, plus a
"Complete" button.
"""

import customtkinter as ctk
from datetime import date

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

class DoctorDashboard(ctk.CTk):
    def __init__(self, doctor):
        super().__init__()
        self.doctor = doctor
        self.appointment_controller = AppointmentController()

        self.title(doctor.dashboard_title())
        self.geometry("900x640")
        self.build_ui()
        self.load_appointments()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            header, text=self.doctor.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=90, command=self.load_appointments
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

    def load_appointments(self):
        self.clear_list()
        try:
            rows = self.appointment_controller.get_schedule_for_doctor(
                self.doctor.user_id, date.today().isoformat()
            )
            appointments = []
            for r in rows:
                record = dict(r)
                patient_name = record.get("patient_name")
                if not patient_name:
                    patient_name = "Patient #" + str(record["patient_id"])
                appointments.append({
                    "id": record["id"],
                    "time": record["scheduled_time"].strftime("%-I:%M %p"),
                    "patient": patient_name,
                    "reason": record["reason"],
                    "status": record["status"],
                })
        except AppointMedError:
            appointments = []

        if not appointments:
            ctk.CTkLabel(
                self.list_frame, text="No appointments scheduled for today.",
                text_color="gray50"
            ).pack(pady=40)
            return

        for appt in appointments:
            self.add_appointment_card(appt)

    def add_appointment_card(self, appt):
        card = ctk.CTkFrame(self.list_frame, corner_radius=10)
        card.pack(fill="x", pady=6)

        ctk.CTkLabel(
            card, text=appt["time"], width=90,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(16, 8), pady=14)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=14)
        ctk.CTkLabel(
            info, text=appt["patient"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text=appt["reason"], font=ctk.CTkFont(size=12), text_color="gray50", anchor="w"
        ).pack(fill="x")

        colors = STATUS_COLORS.get(appt["status"], STATUS_COLORS["Scheduled"])
        bg = colors[0]
        fg = colors[1]
        ctk.CTkLabel(
            card, text=appt["status"], fg_color=bg, text_color=fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        if appt["status"] != "Completed" and appt["status"] != "Cancelled":
            ctk.CTkButton(
                card, text="Complete", width=80, height=26,
                fg_color="#2F855A", hover_color="#276749",
                command=lambda a=appt: self.mark_completed(a)
            ).pack(side="right", padx=(8, 0))

    def mark_completed(self, appt):
        try:
            self.appointment_controller.update_status(appt["id"], "Completed")
        except AppointMedError:
            pass
        self.load_appointments()
