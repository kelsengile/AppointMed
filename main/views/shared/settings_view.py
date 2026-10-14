"""Settings screen (shared by every role): appearance, time format, reminders.

Embed it in a dashboard:  SettingsView(parent, current_user).pack(fill="both", expand=True)
`current_user` needs `.user_id`. Saving applies the appearance mode immediately.
"""
from tkinter import messagebox

import customtkinter as ctk

from controllers.user_controller import UserController
from models.user_settings import (APPEARANCE_MODES, REMINDER_HOURS, TIME_FORMATS,
                                  UserSettings)
from utils.exceptions import AppointMedError


class SettingsView(ctk.CTkFrame):
    """Form for the signed-in user's personal preferences."""

    def __init__(self, parent, current_user, on_saved=None):
        """Build the form and fill it with the user's saved settings.

        Parameters: parent (widget), current_user (object with user_id),
        on_saved (optional callback called after a successful save/reset).
        """
        super().__init__(parent)
        self._user = current_user
        self._controller = UserController()
        self._on_saved = on_saved
        self._build_title()
        self._build_display_section()
        self._build_reminder_section()
        self._build_buttons()
        self._load()

    # ---- layout --------------------------------------------------------
    def _build_title(self):
        """Create the page title."""
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=16, pady=(16, 8))

    def _build_display_section(self):
        """Create the appearance and time-format drop-downs."""
        card = self._new_section("Display")
        self._appearance = self._add_menu(card, "Appearance", list(APPEARANCE_MODES))
        self._time_format = self._add_menu(card, "Time format", list(TIME_FORMATS))

    def _build_reminder_section(self):
        """Create the reminder switch and 'remind me' drop-down."""
        card = self._new_section("Reminders")
        self._email_switch = ctk.CTkSwitch(card, text="Email reminders")
        self._email_switch.pack(anchor="w", padx=16, pady=8)
        self._reminder = self._add_menu(
            card, "Remind me (hours before)", [str(h) for h in REMINDER_HOURS])

    def _build_buttons(self):
        """Create the Save and Reset buttons."""
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=12)
        ctk.CTkButton(row, text="Save changes", command=self._on_save).pack(side="left")
        ctk.CTkButton(row, text="Reset to defaults", fg_color="gray40",
                      command=self._on_reset).pack(side="left", padx=12)

    def _new_section(self, title):
        """Create a titled card frame.

        Parameters: title (str).
        Returns: the CTkFrame to place controls in.
        """
        card = ctk.CTkFrame(self)
        card.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=15, weight="bold")
                     ).pack(anchor="w", padx=16, pady=(12, 0))
        return card

    def _add_menu(self, card, label, values):
        """Add a labelled drop-down to a card.

        Parameters: card (frame), label (str), values (list of str).
        Returns: the CTkOptionMenu.
        """
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, width=190, anchor="w").pack(side="left")
        menu = ctk.CTkOptionMenu(row, values=values)
        menu.pack(side="left")
        return menu

    # ---- data ----------------------------------------------------------
    def _load(self):
        """Fetch the saved settings and show them in the form."""
        try:
            self._show(self._controller.get_settings(self._user.user_id))
        except AppointMedError as err:
            messagebox.showerror("AppointMed", str(err))

    def _show(self, settings):
        """Fill the form from a UserSettings object and apply its appearance mode.

        Parameters: settings (UserSettings).
        """
        self._appearance.set(settings.appearance_mode)
        self._time_format.set(settings.time_format)
        self._reminder.set(str(settings.reminder_hours))
        self._email_switch.select() if settings.email_reminders else self._email_switch.deselect()
        ctk.set_appearance_mode(settings.appearance_mode)

    def _read_form(self):
        """Collect the form values into a UserSettings object.

        Returns: UserSettings.
        """
        return UserSettings(self._appearance.get(), self._time_format.get(),
                            bool(self._email_switch.get()), int(self._reminder.get()))

    # ---- events --------------------------------------------------------
    def _on_save(self):
        """Validate and save the form, then apply it."""
        try:
            saved = self._controller.save_settings(self._user.user_id, self._read_form())
        except AppointMedError as err:
            messagebox.showerror("AppointMed", str(err))
            return
        self._show(saved)
        messagebox.showinfo("Settings", "Settings saved.")
        self._notify()

    def _on_reset(self):
        """Reset to defaults after confirmation."""
        if not messagebox.askyesno("Reset settings", "Reset all settings to defaults?"):
            return
        try:
            self._show(self._controller.reset_settings(self._user.user_id))
        except AppointMedError as err:
            messagebox.showerror("AppointMed", str(err))
            return
        self._notify()

    def _notify(self):
        """Tell the host screen the settings changed (e.g. so History reloads)."""
        if self._on_saved:
            self._on_saved()