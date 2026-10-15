"""
Invoice page - shared by the Admin, Doctor and Nurse dashboards.

Every role gets the same screen; what changes is what they can see and do:

    Role     Sees                              Can do
    -------  --------------------------------  ------------------------------
    Admin    every doctor's invoices           issue, mark paid, cancel
    Nurse    their assigned doctor's invoices  issue, mark paid, cancel
    Doctor   invoices for their own patients   view only

Use it from a dashboard like this (the user object tells the page which
role it is serving):

    def build_invoice_page(self, parent):
        return InvoicePage(parent, self.nurse)

The page is a CTkFrame, so the dashboard's build_content_area() can place()
it exactly like any other page. All database work goes through
InvoiceController - there is no SQL in this file.
"""

import customtkinter as ctk
from tkinter import messagebox

from controllers.invoice_controller import InvoiceController
from models.user import Admin, Nurse
from utils.exceptions import AppointMedError
from utils.formatting import format_datetime

# ---------------------------------------------------------------------------
# SETTINGS - change a colour or the currency in ONE place
# ---------------------------------------------------------------------------
CURRENCY = "₱"
AUTO_REFRESH_MS = 30000     # re-read the database every 30 s so a bill issued
                            # on another machine shows up without pressing Refresh

MUTED_TEXT = "gray50"
ERROR_TEXT = "#d64545"
SUCCESS_TEXT = "#2F855A"
REFRESH_BG = "gray60"
PAID_BG, PAID_HOVER = "#2F855A", "#276749"
CANCEL_BG, CANCEL_HOVER = "#C53030", "#9B2C2C"

STATUS_FILTERS = ["All", "Unpaid", "Paid", "Cancelled"]
# status -> (badge background, badge text)
STATUS_COLORS = {
    "Unpaid": ("#FFF6DC", "#B7791F"),
    "Paid": ("#E3F6E8", "#2F855A"),
    "Cancelled": ("#FBE7E7", "#C53030"),
}


def money(value):
    """Decimal/float -> "₱1,250.50"."""
    return CURRENCY + format(float(value), ",.2f")


class InvoicePage(ctk.CTkFrame):

    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.controller = InvoiceController()
        self._after_id = None

        self._work_out_access()
        self._build()
        self.load_invoices()
        self._after_id = self.after(AUTO_REFRESH_MS, self._auto_refresh)

    # ------------------------------------------------------------------
    # Who is this, and what are they allowed to do?
    # ------------------------------------------------------------------
    def _work_out_access(self):
        self.unassigned = False
        if isinstance(self.user, Admin):
            self.doctor_scope = None            # None = every doctor
            self.can_manage = True
            self.subtitle = "Session invoices for every doctor in the clinic."
        elif isinstance(self.user, Nurse):
            self.doctor_scope = self.user.assigned_doctor_id
            self.can_manage = True
            self.unassigned = self.doctor_scope is None
            self.subtitle = "Session invoices for your assigned doctor's patients."
        else:                                   # Doctor
            self.doctor_scope = self.user.user_id
            self.can_manage = False
            self.subtitle = "Invoices for your patients. Billing is handled by your nurse."

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text="Billing & Invoices",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        if self.can_manage:
            ctk.CTkButton(
                header, text="+ Issue invoice", width=130,
                command=self.open_issue_form
            ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color=REFRESH_BG,
            command=self.load_invoices
        ).pack(side="right", padx=(8, 0))

        self.filter_menu = ctk.CTkOptionMenu(
            header, values=STATUS_FILTERS, width=110,
            command=lambda _choice: self.load_invoices()
        )
        self.filter_menu.pack(side="right")

        ctk.CTkLabel(
            self, text=self.subtitle,
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # Summary tiles
        tiles = ctk.CTkFrame(self, fg_color="transparent")
        tiles.pack(fill="x", padx=24, pady=(0, 12))
        self.tile_labels = {}
        for key, caption in (("unpaid_total", "Outstanding"),
                             ("paid_total", "Collected"),
                             ("unpaid_count", "Unpaid invoices")):
            tile = ctk.CTkFrame(tiles, corner_radius=10)
            tile.pack(side="left", fill="x", expand=True, padx=(0, 10))
            ctk.CTkLabel(
                tile, text=caption, font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
            ).pack(anchor="w", padx=14, pady=(10, 0))
            value = ctk.CTkLabel(tile, text="-", font=ctk.CTkFont(size=20, weight="bold"))
            value.pack(anchor="w", padx=14, pady=(0, 10))
            self.tile_labels[key] = value

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    # ------------------------------------------------------------------
    # Loading + drawing the list
    # ------------------------------------------------------------------
    def load_invoices(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if self.unassigned:
            self._show_message("You are not assigned to a doctor yet, so there are no invoices to show.")
            self._show_summary({"unpaid_total": 0, "paid_total": 0, "unpaid_count": 0})
            return

        status = self.filter_menu.get()
        status = None if status == "All" else status
        try:
            invoices = self.controller.get_invoices(self.doctor_scope, status)
            summary = self.controller.get_summary(self.doctor_scope)
        except AppointMedError as e:
            self._show_message(str(e), color=ERROR_TEXT)
            return

        self._show_summary(summary)
        if not invoices:
            self._show_message("No invoices found.")
            return
        for invoice in invoices:
            self._add_invoice_row(invoice)

    def _show_summary(self, summary):
        self.tile_labels["unpaid_total"].configure(text=money(summary["unpaid_total"]))
        self.tile_labels["paid_total"].configure(text=money(summary["paid_total"]))
        self.tile_labels["unpaid_count"].configure(text=str(summary["unpaid_count"]))

    def _show_message(self, text, color=MUTED_TEXT):
        ctk.CTkLabel(
            self.list_frame, text=text, text_color=color, wraplength=600
        ).pack(pady=40)

    def _add_invoice_row(self, inv):
        row = ctk.CTkFrame(self.list_frame, corner_radius=10)
        row.pack(fill="x", pady=5)

        # Packed right-to-left: buttons, badge, amount - then the text takes the rest.
        if self.can_manage and inv.is_unpaid():
            ctk.CTkButton(
                row, text="Cancel", width=70, fg_color=CANCEL_BG, hover_color=CANCEL_HOVER,
                command=lambda i=inv: self.cancel_invoice(i)
            ).pack(side="right", padx=(0, 14))
            ctk.CTkButton(
                row, text="Mark paid", width=90, fg_color=PAID_BG, hover_color=PAID_HOVER,
                command=lambda i=inv: self.mark_paid(i)
            ).pack(side="right", padx=(0, 8))

        badge_bg, badge_fg = STATUS_COLORS.get(inv.status, ("#EEF1F4", "#4A5568"))
        ctk.CTkLabel(
            row, text=inv.status, fg_color=badge_bg, text_color=badge_fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=14)

        ctk.CTkLabel(
            row, text=money(inv.amount), font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="right", padx=(0, 6))

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            info, text="Invoice #" + str(inv.invoice_id) + " — " + str(inv.patient_name),
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")

        parts = ["Appointment #" + str(inv.appointment_id),
                 "Dr. " + str(inv.doctor_name),
                 "Issued by " + str(inv.issued_by_name)]
        if inv.issued_at:
            parts.append(format_datetime(inv.issued_at, "%b %d, %Y"))
        if inv.status == "Paid" and inv.paid_at:
            parts.append("Paid " + format_datetime(inv.paid_at, "%b %d, %Y"))
        ctk.CTkLabel(
            info, text="  ·  ".join(parts),
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def mark_paid(self, inv):
        sure = messagebox.askyesno(
            "Mark as paid",
            "Mark invoice #" + str(inv.invoice_id) + " (" + money(inv.amount) + ") as paid?",
            parent=self.winfo_toplevel()
        )
        if sure:
            self._run(lambda: self.controller.mark_paid(inv.invoice_id))

    def cancel_invoice(self, inv):
        sure = messagebox.askyesno(
            "Cancel invoice",
            "Cancel invoice #" + str(inv.invoice_id) + "? This can't be undone.",
            parent=self.winfo_toplevel()
        )
        if sure:
            self._run(lambda: self.controller.cancel_invoice(inv.invoice_id))

    def _run(self, action):
        try:
            action()
        except AppointMedError as e:
            messagebox.showerror("Invoice", str(e), parent=self.winfo_toplevel())
        self.load_invoices()

    def open_issue_form(self):
        if self.unassigned:
            messagebox.showinfo("Invoice", "You are not assigned to a doctor yet.",
                                parent=self.winfo_toplevel())
            return
        try:
            appointments = self.controller.get_billable_appointments(self.doctor_scope)
        except AppointMedError as e:
            messagebox.showerror("Invoice", str(e), parent=self.winfo_toplevel())
            return
        if not appointments:
            messagebox.showinfo(
                "Nothing to bill",
                "No appointments are waiting to be billed.\n\n"
                "An appointment can be invoiced once the doctor has examined the patient.",
                parent=self.winfo_toplevel()
            )
            return

        # dropdown text -> appointment id
        choices = {}
        for a in appointments:
            label = ("#" + str(a["id"]) + "  ·  " + a["patient_name"] + "  ·  Dr. "
                     + a["doctor_name"] + "  ·  " + format_datetime(a["scheduled_time"], "%b %d"))
            choices[label] = a["id"]

        form = ctk.CTkToplevel(self)
        form.title("Issue Invoice")
        form.geometry("480x340")
        form.resizable(False, False)
        form.transient(self.winfo_toplevel())
        form.after(100, form.grab_set)      # modal; waits until the window is visible

        ctk.CTkLabel(
            form, text="Create New Invoice", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 12))

        ctk.CTkLabel(form, text="Appointment to bill", anchor="w").pack(fill="x", padx=30, pady=(6, 2))
        appointment_menu = ctk.CTkOptionMenu(form, values=list(choices), width=420, dynamic_resizing=False)
        appointment_menu.pack(padx=30)

        ctk.CTkLabel(form, text="Amount (" + CURRENCY + ")", anchor="w").pack(fill="x", padx=30, pady=(12, 2))
        amount_entry = ctk.CTkEntry(form, width=420, placeholder_text="e.g. 500.00")
        amount_entry.pack(padx=30)

        status_label = ctk.CTkLabel(form, text="", text_color=ERROR_TEXT, wraplength=420)
        status_label.pack(pady=(10, 0))

        def submit():
            try:
                self.controller.create_invoice(
                    appointment_id=choices[appointment_menu.get()],
                    issued_by=self.user.user_id,
                    amount=amount_entry.get(),
                )
            except AppointMedError as e:
                status_label.configure(text=str(e))
                return
            form.destroy()
            self.load_invoices()

        amount_entry.bind("<Return>", lambda _event: submit())
        ctk.CTkButton(form, text="Issue Invoice", command=submit).pack(pady=18)

    # ------------------------------------------------------------------
    # Auto refresh + clean-up
    # ------------------------------------------------------------------
    def _auto_refresh(self):
        self.load_invoices()
        self._after_id = self.after(AUTO_REFRESH_MS, self._auto_refresh)

    def destroy(self):
        # Stop the timer first, or it fires on a window that no longer exists.
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        super().destroy()
