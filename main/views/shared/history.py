"""History screen (shared by every role): past appointments table.

Embed it in a dashboard:  HistoryView(parent, current_user).pack(fill="both", expand=True)
`current_user` needs `.user_id` and `.role` ('admin' | 'doctor' | 'nurse').
Doctors see only their own history; only Admins get the delete buttons.
"""
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from controllers.appointment_controller import AppointmentController
from controllers.user_controller import UserController

ALL_STATUSES = "All statuses"
PER_PAGE = 15
SEARCH_DELAY_MS = 300
COLUMNS = (("date", "Date", 100), ("time", "Time", 90), ("patient", "Patient", 170),
           ("doctor", "Doctor", 150), ("status", "Status", 100), ("reason", "Reason", 240))


class HistoryView(ctk.CTkFrame):
    """Searchable, paged table of completed and cancelled appointments."""

    def __init__(self, parent, current_user):
        """Build the screen and load the first page.

        Parameters: parent (widget), current_user (object with user_id and role).
        """
        super().__init__(parent)
        self._user = current_user
        self._appointments = AppointmentController()
        self._page = 1
        self._total_pages = 1
        self._search_job = None
        self._time_format = self._load_time_format()
        self._build_header()
        self._build_filters()
        self._build_table()
        self._build_pager()
        self.refresh()

    # ---- layout --------------------------------------------------------
    def _build_header(self):
        """Create the title and, for Admins, the delete buttons."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="Appointment History",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        if self._is_admin():
            ctk.CTkButton(header, text="Clear history", fg_color="#c0392b",
                          hover_color="#962d22", command=self._on_clear).pack(side="right")
            ctk.CTkButton(header, text="Delete selected", width=120,
                          command=self._on_delete_selected).pack(side="right", padx=8)

    def _build_filters(self):
        """Create the search box and status drop-down."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=4)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)
        ctk.CTkEntry(bar, textvariable=self._search_var, width=320,
                     placeholder_text="Search patient, doctor or reason...").pack(side="left")
        self._status_menu = ctk.CTkOptionMenu(
            bar, values=[ALL_STATUSES, *AppointmentController.HISTORY_STATUSES],
            command=lambda _choice: self._reset_to_first_page())
        self._status_menu.pack(side="left", padx=12)

    def _build_table(self):
        """Create the Treeview table (CustomTkinter has no table widget)."""
        holder = ctk.CTkFrame(self)
        holder.pack(fill="both", expand=True, padx=16, pady=8)
        self._tree = ttk.Treeview(holder, columns=[c[0] for c in COLUMNS],
                                  show="headings", selectmode="browse")
        for key, title, width in COLUMNS:
            self._tree.heading(key, text=title)
            self._tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._empty_label = ctk.CTkLabel(self, text="No past appointments found.",
                                         text_color="gray")

    def _build_pager(self):
        """Create the Prev / page label / Next controls."""
        pager = ctk.CTkFrame(self, fg_color="transparent")
        pager.pack(pady=(0, 12))
        self._prev_btn = ctk.CTkButton(pager, text="< Prev", width=80, command=self._go_prev)
        self._prev_btn.pack(side="left")
        self._page_label = ctk.CTkLabel(pager, text="")
        self._page_label.pack(side="left", padx=16)
        self._next_btn = ctk.CTkButton(pager, text="Next >", width=80, command=self._go_next)
        self._next_btn.pack(side="left")

    # ---- data ----------------------------------------------------------
    def refresh(self):
        """Reload the current page from the database and redraw the table."""
        self._style_table()
        try:
            rows, self._total_pages = self._appointments.get_history(
                doctor_id=self._doctor_filter(), status=self._selected_status(),
                search=self._search_var.get(), page=self._page, per_page=PER_PAGE)
        except Exception as err:  # controllers raise our custom exceptions
            self._show_error(err)
            return
        self._tree.delete(*self._tree.get_children())
        for row in rows:
            when = row["scheduled_time"]
            self._tree.insert("", "end", iid=str(row["id"]), values=(
                when.strftime("%Y-%m-%d"), self._format_time(when), row["full_name"],
                row["doctor_name"], row["status"], row.get("reason") or ""))
        self._update_pager(bool(rows))

    def _format_time(self, moment):
        """Return a datetime's time as text in the user's preferred format.

        Parameters: moment (datetime).
        Returns: str such as '2:30 PM' (12h) or '14:30' (24h).
        """
        if self._time_format == "24h":
            return moment.strftime("%H:%M")
        return moment.strftime("%I:%M %p").lstrip("0")

    def _load_time_format(self):
        """Return the user's saved time format, falling back to '12h' on error."""
        try:
            return UserController().get_settings(self._user.user_id).time_format
        except Exception:  # settings are optional; never block the history page
            return "12h"

    def _selected_status(self):
        """Return the chosen status filter, or None for all."""
        choice = self._status_menu.get()
        return None if choice == ALL_STATUSES else choice

    def _doctor_filter(self):
            """Doctor id to filter by: a doctor's own id, a nurse's assigned
            doctor, or None (admin sees everyone)."""
            if self._user.role == "doctor":
                return self._user.user_id
            if self._user.role == "nurse":
                return self._user.assigned_doctor_id
            return None
    
    def reload_settings(self):
        """Re-read the saved time format, then redraw (called after Settings saves)."""
        self._time_format = self._load_time_format()
        self.refresh()

    def _is_admin(self):
        """Return True if the signed-in user is an Admin."""
        return self._user.role == "admin"

    # ---- events --------------------------------------------------------
    def _on_search_changed(self, *_args):
        """Wait briefly after typing stops, then search from page 1."""
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(SEARCH_DELAY_MS, self._reset_to_first_page)

    def _reset_to_first_page(self):
        """Jump back to page 1 and reload (used when a filter changes)."""
        self._page = 1
        self.refresh()

    def _go_prev(self):
        """Show the previous page."""
        self._page -= 1
        self.refresh()

    def _go_next(self):
        """Show the next page."""
        self._page += 1
        self.refresh()

    def _on_delete_selected(self):
        """Delete the highlighted row after confirmation (Admin only)."""
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("Delete record", "Select a row first.")
            return
        if not messagebox.askyesno("Delete record", "Delete this history record?"):
            return
        try:
            self._appointments.delete_history_record(int(selected[0]))
        except Exception as err:  # controllers raise our custom exceptions
            self._show_error(err)
        self.refresh()

    def _on_clear(self):
        """Delete all history after confirmation (Admin only)."""
        if not messagebox.askyesno("Clear history",
                                   "Delete ALL past appointment records? This cannot be undone."):
            return
        try:
            removed = self._appointments.clear_history()
            messagebox.showinfo("Clear history", f"Removed {removed} records.")
        except Exception as err:  # controllers raise our custom exceptions
            self._show_error(err)
        self._reset_to_first_page()

    # ---- presentation helpers -----------------------------------------
    def _update_pager(self, has_rows):
        """Update the page label, button states and empty-state message."""
        self._page_label.configure(text=f"Page {self._page} of {self._total_pages}")
        self._prev_btn.configure(state="normal" if self._page > 1 else "disabled")
        self._next_btn.configure(state="normal" if self._page < self._total_pages else "disabled")
        if has_rows:
            self._empty_label.pack_forget()
        else:
            self._empty_label.pack(pady=8)

    def _style_table(self):
        """Match the Treeview colours to the current light/dark appearance."""
        dark = ctk.get_appearance_mode() == "Dark"
        bg, fg, head = ("#2b2b2b", "#e8e8e8", "#3a3a3a") if dark else ("#ffffff", "#1c1c1c", "#e6e6e6")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg,
                        rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background=head, foreground=fg, relief="flat")
        style.map("Treeview", background=[("selected", "#1f6aa5")])

    def _show_error(self, err):
        """Show a controller error to the user in a message box."""
        messagebox.showerror("AppointMed", str(err))