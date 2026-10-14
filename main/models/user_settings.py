"""
Plain data class for one user's saved preferences. No Tkinter, no SQL.
The allowed values live here so the view's drop-downs and the controller's
validation always agree.
"""

APPEARANCE_MODES = ("Light", "Dark", "System")
TIME_FORMATS = ("12h", "24h")
REMINDER_HOURS = (1, 2, 6, 12, 24, 48)


class UserSettings:
    """One user's preferences (appearance, time format, reminders)."""

    def __init__(self, appearance_mode="Light", time_format="12h",
                 email_reminders=True, reminder_hours=24):
        self.appearance_mode = appearance_mode
        self.time_format = time_format
        self.email_reminders = email_reminders
        self.reminder_hours = reminder_hours

    @classmethod
    def from_row(cls, row):
        """Build a UserSettings from a user_settings database row (dict)."""
        return cls(
            appearance_mode=row["appearance_mode"],
            time_format=row["time_format"],
            email_reminders=bool(row["email_reminders"]),
            reminder_hours=int(row["reminder_hours"]),
        )