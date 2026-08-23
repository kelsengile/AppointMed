"""
Nurse/Secretary dashboard — CustomTkinter version.
Scoped to nurse.assigned_doctor_id: this nurse only ever sees and manages
one doctor's schedule. Includes an "Add appointment" form since this is
the role that books appointments on the doctor's behalf.
"""

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

SAMPLE_APPOINTMENTS = [
    {"id": 1, "time": "9:00 AM", "patient": "Liam Mercado", "reason": "Follow-up checkup", "status": "Checked-in"},
    {"id": 2, "time": "9:30 AM", "patient": "Rosa Torres", "reason": "New patient consult", "status": "Scheduled"},
]


class NurseDashboard(ctk.CTk):
    def __init__(self, nurse):
        super().__init__()
        self.nurse = nurse
        self.appointment_controller = AppointmentController()

        self.title(nurse.dashboard_title())
        self.geometry("900x680")
        self._build_ui()
        self._load_appointments()

    # ---------- layout ----------

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text=self.nurse.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Add appointment", width=150,
            command=self._open_add_form
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color="gray60",
            command=self._load_appointments
        ).pack(side="right")

        ctk.CTkLabel(
            self, text=f"Managing schedule for Doctor #{self.nurse.assigned_doctor_id} — "
                       f"{date.today().strftime('%A, %B %d')}",
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
                self.nurse.assigned_doctor_id, date.today().isoformat()
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
            appointments = SAMPLE_APPOINTMENTS

        if not appointments:
            ctk.CTkLabel(
                self.list_frame, text="No appointments scheduled for today.",
                text_color="gray50"
            ).pack(pady=40)
            return

        for appt in appointments:
            self._add_appointment_card(appt)

    # ---------- appointment cards ----------

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
        ctk.CTkLabel(
            card, text=appt["status"], fg_color=bg, text_color=fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        if appt["status"] not in ("Completed", "Cancelled"):
            ctk.CTkButton(
                card, text="Cancel", width=70, height=26,
                fg_color="#C53030", hover_color="#9B2C2C",
                command=lambda a=appt: self._cancel_appointment(a)
            ).pack(side="right", padx=(8, 0))

    def _cancel_appointment(self, appt):
        try:
            self.appointment_controller.update_status(appt["id"], "Cancelled")
        except AppointMedError as e:
            messagebox.showerror("Error", str(e))
        self._load_appointments()

    # ---------- add appointment form ----------

    def _open_add_form(self):
        form = ctk.CTkToplevel(self)
        form.title("Add Appointment")
        form.geometry("380x420")
        form.grab_set()  # modal

        ctk.CTkLabel(
            form, text="New Appointment", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 16))

        patient_id_entry = self._labeled_entry(form, "Patient ID")
        time_entry = self._labeled_entry(form, "Date & time (YYYY-MM-DD HH:MM)")
        reason_entry = self._labeled_entry(form, "Reason")

        status_label = ctk.CTkLabel(form, text="", text_color="#d64545")
        status_label.pack(pady=(4, 0))

        def submit():
            try:
                patient_id = int(patient_id_entry.get().strip())
                scheduled_time = datetime.strptime(
                    time_entry.get().strip(), "%Y-%m-%d %H:%M"
                )
                reason = reason_entry.get().strip()
                if not reason:
                    raise ValueError("Reason is required.")

                self.appointment_controller.add_appointment(
                    patient_id, self.nurse.assigned_doctor_id, scheduled_time, reason
                )
                form.destroy()
                self._load_appointments()
            except AppointMedError as e:
                status_label.configure(text=str(e))
            except ValueError:
                status_label.configure(text="Check your input format and try again.")

        ctk.CTkButton(form, text="Add appointment", command=submit).pack(pady=24)

    def _labeled_entry(self, parent, label_text):
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(
            fill="x", padx=30, pady=(10, 2)
        )
        entry = ctk.CTkEntry(parent, width=300)
        entry.pack(padx=30)
        return entry
