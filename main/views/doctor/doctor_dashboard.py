"""
Doctor's dashboard — CustomTkinter version.
Shows today's appointments as cards with status badges, plus quick
actions (mark completed / cancel). Pulls real data through
AppointmentController; falls back to sample rows if the DB isn't
reachable yet, so you can preview the UI before MySQL is fully wired up.
"""

import customtkinter as ctk
from datetime import datetime, date

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

# Used only if the database isn't reachable yet, so the UI is still previewable
SAMPLE_APPOINTMENTS = [
    {"id": 1, "time": "9:00 AM", "patient": "Liam Mercado", "reason": "Follow-up checkup", "status": "Checked-in"},
    {"id": 2, "time": "9:30 AM", "patient": "Rosa Torres", "reason": "New patient consult", "status": "Scheduled"},
    {"id": 3, "time": "10:15 AM", "patient": "Kian Ang", "reason": "Vaccination", "status": "Scheduled"},
]


class DoctorDashboard(ctk.CTk):
    def __init__(self, doctor):
        super().__init__()
        self.doctor = doctor
        self.appointment_controller = AppointmentController()

        self.title(doctor.dashboard_title())
        self.geometry("900x640")
        self._build_ui()
        self._load_appointments()

    # ---------- layout ----------

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            header, text=self.doctor.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=90, command=self._load_appointments
        ).pack(side="right")

        ctk.CTkLabel(
            self, text=f"Today — {date.today().strftime('%A, %B %d')}",
            font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def _clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    # ---------- data ----------

    def _load_appointments(self):
        self._clear_list()
        try:
            rows = self.appointment_controller.get_schedule_for_doctor(
                self.doctor.user_id, date.today().isoformat()
            )
            appointments = [
                {
                    "id": r["id"],
                    "time": r["scheduled_time"].strftime("%-I:%M %p"),
                    "patient": r.get("patient_name", f"Patient #{r['patient_id']}"),
                    "reason": r["reason"],
                    "status": r["status"],
                }
                for r in rows
            ]
        except AppointMedError:
            # DB not reachable yet — preview with sample data instead of an empty screen
            appointments = SAMPLE_APPOINTMENTS

        if not appointments:
            ctk.CTkLabel(
                self.list_frame, text="No appointments scheduled for today.",
                text_color="gray50"
            ).pack(pady=40)
            return

        for appt in appointments:
            self._add_appointment_card(appt)

    # ---------- UI pieces ----------

    def _add_appointment_card(self, appt):
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

        bg, fg = STATUS_COLORS.get(appt["status"], STATUS_COLORS["Scheduled"])
        badge = ctk.CTkLabel(
            card, text=appt["status"], fg_color=bg, text_color=fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        badge.pack(side="right", padx=(8, 16))

        if appt["status"] not in ("Completed", "Cancelled"):
            ctk.CTkButton(
                card, text="Complete", width=80, height=26,
                fg_color="#2F855A", hover_color="#276749",
                command=lambda a=appt: self._mark_completed(a)
            ).pack(side="right", padx=(8, 0))

    def _mark_completed(self, appt):
        try:
            self.appointment_controller.update_status(appt["id"], "Completed")
        except AppointMedError:
            pass  # in sample/offline mode there's nothing to persist
        self._load_appointments()


if __name__ == "__main__":
    # Quick standalone preview using a fake doctor object, so you can see
    # the UI without needing a live login flow.
    class _FakeDoctor:
        user_id = 1
        def dashboard_title(self):
            return "Dr. Juan Diaz — Pediatrics"

    DoctorDashboard(_FakeDoctor()).mainloop()
