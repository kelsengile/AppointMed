"""
"My Account" page, shared by the Admin, Doctor and Nurse dashboards so
every role gets the same (better) profile screen.

    +--------------------------------------------------------+
    |  (photo)   Dr. Juan Diaz                               |
    |            @jdiaz                                      |
    |            [Doctor]  Member since March 2026           |
    |            [Change photo]  [Remove photo]              |
    +--------------------------------------------------------+
    |  Profile details                                       |
    |  Full name [__________]     Username [__________]      |
    |  Specialization [_________________________]  (doctors) |
    |  [Save changes]  [Reset]                               |
    +--------------------------------------------------------+
    |  Change password                                       |
    |  Current / New (with strength bar) / Confirm           |
    |  [ ] Show passwords            [Update password]       |
    +--------------------------------------------------------+

What a user can change here: profile picture, full name, username,
specialization (doctors) and password. Everything is saved through
UserController; this file only draws the screen.

HOW A DASHBOARD USES IT
    self.profile_page = ProfilePage(
        parent, user, "doctor", self.user_controller,
        avatar_bytes=self.avatar_bytes,       # already loaded for the sidebar
        on_change=self.on_profile_changed,    # called after any successful save
    )
When on_change fires, the page has already updated `user.full_name`,
`user.username` (and `user.specialization`) in place and refreshed its own
`avatar_bytes`, so the dashboard only has to redraw its sidebar/title.
"""

from tkinter import filedialog

import customtkinter as ctk

from utils.avatar import prepare_avatar, render_avatar
from utils.exceptions import AppointMedError


# ===========================================================================
# SETTINGS
# ===========================================================================
CARD_BG = "white"
CARD_BORDER = "#E2E8F0"
TITLE_TEXT = "#1A202C"
LABEL_TEXT = "#4A5568"
MUTED_TEXT = "gray50"
ERROR_TEXT = "#d64545"
SUCCESS_TEXT = "#2F855A"
SECONDARY_BG = "gray60"
SECONDARY_HOVER = "gray50"

# Per role: badge text, badge background, and the accent colour used for
# the photo ring / initials.
ROLE_STYLES = {
    "doctor": {"label": "Doctor", "bg": "#E3F0FF", "fg": "#2B6CB0"},
    "nurse": {"label": "Nurse", "bg": "#F3E8FF", "fg": "#6B46C1"},
    "admin": {"label": "Administrator", "bg": "#FBE7E7", "fg": "#C53030"},
}

PHOTO_TYPES = [
    ("Pictures", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
    ("All files", "*.*"),
]

# Password strength bar: (label, colour) for scores 1..5.
STRENGTH_LEVELS = {
    1: ("Weak", "#d64545"),
    2: ("Weak", "#d64545"),
    3: ("Fair", "#DD8B1B"),
    4: ("Good", "#2C7A7B"),
    5: ("Strong", "#2F855A"),
}


def password_strength(password):
    """0-5: one point each for length >= 6, length >= 10, upper AND lower
    case, a digit, and a symbol. Just a hint for the user - the only rule
    actually enforced is the minimum length in UserController."""
    if not password:
        return 0
    score = 0
    if len(password) >= 6:
        score += 1
    if len(password) >= 10:
        score += 1
    if any(c.islower() for c in password) and any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(not c.isalnum() for c in password):
        score += 1
    return score


class ProfilePage(ctk.CTkScrollableFrame):
    AVATAR_SIZE = 104

    def __init__(self, parent, user, role, user_controller,
                 avatar_bytes=None, on_change=None):
        # A scrollable frame so the page can grow past the window height
        # without anything getting cut off.
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.role = role if role in ROLE_STYLES else "admin"
        self.style = ROLE_STYLES[self.role]
        self.controller = user_controller
        self.avatar_bytes = avatar_bytes
        self.on_change = on_change

        self.member_since = ""
        self.assigned_doctor = None
        self._load_account_info()

        self._build_header()
        self._build_hero_card()
        self._build_details_card()
        self._build_password_card()

    # -------------------------------------------------------------------
    # Small helpers
    # -------------------------------------------------------------------
    def _load_account_info(self):
        """Read-only extras shown on the hero card: when the account was
        created and (for nurses) which doctor they support. Failing to
        load them is not worth breaking the page over."""
        try:
            row = self.controller.get_user_by_id(self.user.user_id)
            created = row.get("created_at")
            if created is not None:
                self.member_since = created.strftime("%B %Y")
        except AppointMedError:
            pass

        doctor_id = getattr(self.user, "assigned_doctor_id", None)
        if self.role == "nurse" and doctor_id:
            try:
                self.assigned_doctor = self.controller.get_user_by_id(doctor_id)["full_name"]
            except AppointMedError:
                pass

    def _card(self):
        card = ctk.CTkFrame(
            self, fg_color=CARD_BG, corner_radius=14,
            border_width=1, border_color=CARD_BORDER
        )
        card.pack(fill="x", padx=24, pady=(0, 16))
        return card

    @staticmethod
    def _section_header(card, title, subtitle):
        ctk.CTkLabel(
            card, text=title, anchor="w", text_color=TITLE_TEXT,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(fill="x", padx=28, pady=(24, 0))
        ctk.CTkLabel(
            card, text=subtitle, anchor="w", text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=12)
        ).pack(fill="x", padx=28, pady=(2, 8))

    @staticmethod
    def _say(label, text, ok):
        """Show a green (ok) or red status message under a form/button."""
        label.configure(text=text, text_color=SUCCESS_TEXT if ok else ERROR_TEXT)

    def _notify(self):
        if self.on_change is not None:
            self.on_change()

    # -------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------
    def _build_header(self):
        ctk.CTkLabel(
            self, text="My Account", anchor="w",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(
            self, text="Manage your photo, personal details and password",
            anchor="w", font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(fill="x", padx=24, pady=(0, 16))

    # -------------------------------------------------------------------
    # Hero card: photo, name, username, role, photo buttons
    # -------------------------------------------------------------------
    def _build_hero_card(self):
        card = self._card()
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=28)

        # fg_color="transparent" so the round photo's corners show the
        # card's white instead of a square of some other colour.
        self.avatar_label = ctk.CTkLabel(
            row, text="", width=self.AVATAR_SIZE, height=self.AVATAR_SIZE,
            fg_color="transparent"
        )
        self.avatar_label.pack(side="left", anchor="n")

        column = ctk.CTkFrame(row, fg_color="transparent")
        column.pack(side="left", fill="x", expand=True, padx=(24, 0))

        self.hero_name = ctk.CTkLabel(
            column, text=self.user.full_name, anchor="w", text_color=TITLE_TEXT,
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.hero_name.pack(fill="x")

        self.hero_username = ctk.CTkLabel(
            column, text="@" + self.user.username, anchor="w",
            text_color=MUTED_TEXT, font=ctk.CTkFont(size=13)
        )
        self.hero_username.pack(fill="x", pady=(0, 8))

        badges = ctk.CTkFrame(column, fg_color="transparent")
        badges.pack(fill="x")
        ctk.CTkLabel(
            badges, text=self.style["label"],
            fg_color=self.style["bg"], text_color=self.style["fg"],
            corner_radius=8, height=24, width=90,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left")

        details = []
        if self.member_since:
            details.append("Member since " + self.member_since)
        if self.assigned_doctor:
            details.append("Assigned doctor: " + self.assigned_doctor)
        if details:
            ctk.CTkLabel(
                badges, text="   ·   ".join(details), anchor="w",
                text_color=MUTED_TEXT, font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=(12, 0))

        buttons = ctk.CTkFrame(column, fg_color="transparent")
        buttons.pack(fill="x", pady=(16, 0))
        ctk.CTkButton(
            buttons, text="Change photo", width=120, height=32,
            command=self.choose_photo
        ).pack(side="left")
        self.remove_photo_btn = ctk.CTkButton(
            buttons, text="Remove photo", width=120, height=32,
            fg_color=SECONDARY_BG, hover_color=SECONDARY_HOVER,
            command=self.remove_photo
        )
        self.remove_photo_btn.pack(side="left", padx=(8, 0))

        self.photo_status = ctk.CTkLabel(
            column, text="", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.photo_status.pack(fill="x", pady=(8, 0))

        self._paint_avatar()

    def _paint_avatar(self):
        """(Re)draw the big round photo, or the initials if there is none,
        and enable "Remove photo" only when there is something to remove."""
        image = render_avatar(
            self.avatar_bytes, self.user.full_name, self.AVATAR_SIZE,
            bg=self.style["fg"], ring_color=self.style["fg"], ring_width=3
        )
        self.avatar_label.configure(image=image)
        self.remove_photo_btn.configure(
            state="normal" if self.avatar_bytes else "disabled"
        )

    def choose_photo(self):
        path = filedialog.askopenfilename(
            title="Choose a profile picture", filetypes=PHOTO_TYPES
        )
        if not path:
            return  # cancelled

        try:
            data = prepare_avatar(path)
            self.controller.set_avatar(self.user.user_id, data)
        except AppointMedError as e:
            self._say(self.photo_status, str(e), ok=False)
            return

        self.avatar_bytes = data
        self._paint_avatar()
        self._say(self.photo_status, "Photo updated.", ok=True)
        self._notify()

    def remove_photo(self):
        try:
            self.controller.remove_avatar(self.user.user_id)
        except AppointMedError as e:
            self._say(self.photo_status, str(e), ok=False)
            return

        self.avatar_bytes = None
        self._paint_avatar()
        self._say(self.photo_status, "Photo removed.", ok=True)
        self._notify()

    # -------------------------------------------------------------------
    # Profile details card: name, username, specialization
    # -------------------------------------------------------------------
    def _field_label(self, parent, text, row, column, columnspan=1, padx=(0, 0)):
        ctk.CTkLabel(
            parent, text=text, anchor="w", text_color=LABEL_TEXT,
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=row, column=column, columnspan=columnspan,
               sticky="w", padx=padx, pady=(10, 2))

    def _build_details_card(self):
        card = self._card()
        self._section_header(
            card, "Profile details",
            "Your name is shown across the app. Your username is what you log in with."
        )

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=28)
        form.grid_columnconfigure((0, 1), weight=1, uniform="fields")

        self._field_label(form, "Full name", 0, 0)
        self.fullname_entry = ctk.CTkEntry(form, height=38)
        self.fullname_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        self._field_label(form, "Username", 0, 1, padx=(8, 0))
        self.username_entry = ctk.CTkEntry(form, height=38)
        self.username_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        next_row = 2
        self.specialization_entry = None
        if self.role == "doctor":
            self._field_label(form, "Specialization", next_row, 0, columnspan=2)
            self.specialization_entry = ctk.CTkEntry(form, height=38)
            self.specialization_entry.grid(
                row=next_row + 1, column=0, columnspan=2, sticky="ew"
            )
            next_row += 2

        ctk.CTkLabel(
            form, text="Usernames use letters, numbers, dots and underscores (3+ characters).",
            anchor="w", text_color=MUTED_TEXT, font=ctk.CTkFont(size=11)
        ).grid(row=next_row, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self._fill_details()

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(16, 24))
        ctk.CTkButton(
            actions, text="Save changes", width=140, height=36,
            command=self.save_details
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Reset", width=90, height=36,
            fg_color=SECONDARY_BG, hover_color=SECONDARY_HOVER,
            command=self._fill_details
        ).pack(side="left", padx=(8, 0))
        self.details_status = ctk.CTkLabel(
            actions, text="", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.details_status.pack(side="left", padx=(14, 0))

    def _fill_details(self):
        """Put the account's current values into the boxes. Also what the
        Reset button does, throwing away anything typed but not saved."""
        for entry, value in (
            (self.fullname_entry, self.user.full_name),
            (self.username_entry, self.user.username),
        ):
            entry.delete(0, "end")
            entry.insert(0, value or "")

        if self.specialization_entry is not None:
            self.specialization_entry.delete(0, "end")
            self.specialization_entry.insert(0, getattr(self.user, "specialization", "") or "")

    def save_details(self):
        username = self.username_entry.get().strip()
        full_name = self.fullname_entry.get().strip()

        specialization = None
        if self.specialization_entry is not None:
            specialization = self.specialization_entry.get().strip()
            if not specialization:
                self._say(self.details_status, "Specialization is required.", ok=False)
                return

        try:
            saved = self.controller.update_profile(
                self.user.user_id, username, full_name, specialization
            )
        except AppointMedError as e:
            self._say(self.details_status, str(e), ok=False)
            return

        # Reflect the change everywhere, without needing to log out and in.
        self.user.username = saved["username"]
        self.user.full_name = saved["full_name"]
        if self.specialization_entry is not None:
            self.user.specialization = saved["specialization"]

        self._fill_details()
        self.hero_name.configure(text=self.user.full_name)
        self.hero_username.configure(text="@" + self.user.username)
        self._paint_avatar()  # initials may have changed with the name
        self._say(self.details_status, "Saved.", ok=True)
        self._notify()

    # -------------------------------------------------------------------
    # Password card
    # -------------------------------------------------------------------
    def _build_password_card(self):
        card = self._card()
        self._section_header(
            card, "Change password",
            "You'll need your current password. Use at least 6 characters."
        )

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=28)
        form.grid_columnconfigure(0, weight=1)

        self.current_password_entry = self._password_row(form, "Current password", 0)
        self.new_password_entry = self._password_row(form, "New password", 2)

        # Strength bar under the new-password box.
        strength_row = ctk.CTkFrame(form, fg_color="transparent")
        strength_row.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        self.strength_bar = ctk.CTkProgressBar(strength_row, height=6)
        self.strength_bar.pack(side="left", fill="x", expand=True)
        self.strength_bar.set(0)
        self.strength_label = ctk.CTkLabel(
            strength_row, text="", width=60, anchor="e",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.strength_label.pack(side="left", padx=(10, 0))
        self.new_password_entry.bind("<KeyRelease>", self._update_strength)

        self.confirm_password_entry = self._password_row(form, "Confirm new password", 5)
        self._password_entries = (
            self.current_password_entry,
            self.new_password_entry,
            self.confirm_password_entry,
        )

        self.show_passwords_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="Show passwords", variable=self.show_passwords_var,
            command=self._toggle_password_visibility,
            font=ctk.CTkFont(size=12), checkbox_width=18, checkbox_height=18
        ).grid(row=7, column=0, sticky="w", pady=(12, 0))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(16, 24))
        ctk.CTkButton(
            actions, text="Update password", width=160, height=36,
            command=self.save_password
        ).pack(side="left")
        self.password_status = ctk.CTkLabel(
            actions, text="", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.password_status.pack(side="left", padx=(14, 0))

    def _password_row(self, form, label, row):
        """Label on `row`, masked entry on `row + 1`. Returns the entry."""
        ctk.CTkLabel(
            form, text=label, anchor="w", text_color=LABEL_TEXT,
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(10, 2))
        entry = ctk.CTkEntry(form, height=38, show="*")
        entry.grid(row=row + 1, column=0, sticky="ew")
        return entry

    def _toggle_password_visibility(self):
        mask = "" if self.show_passwords_var.get() else "*"
        for entry in self._password_entries:
            entry.configure(show=mask)

    def _update_strength(self, event=None):
        score = password_strength(self.new_password_entry.get())
        if score == 0:
            self.strength_bar.set(0)
            self.strength_label.configure(text="")
            return
        label, color = STRENGTH_LEVELS[score]
        self.strength_bar.configure(progress_color=color)
        self.strength_bar.set(score / 5)
        self.strength_label.configure(text=label, text_color=color)

    def save_password(self):
        # .strip() to match the login screen, which strips what is typed -
        # otherwise a password saved with a trailing space could never be
        # typed back in to log in.
        current = self.current_password_entry.get().strip()
        new = self.new_password_entry.get().strip()
        confirm = self.confirm_password_entry.get().strip()

        try:
            self.controller.change_password(self.user.user_id, current, new, confirm)
        except AppointMedError as e:
            self._say(self.password_status, str(e), ok=False)
            return

        for entry in self._password_entries:
            entry.delete(0, "end")
        self._update_strength()
        self._say(self.password_status, "Password updated.", ok=True)