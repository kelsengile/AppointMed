"""
Admin dashboard — built with CustomTkinter.

Lists every Doctor/Nurse/Admin account, and lets the admin add new ones,
including assigning a nurse to a doctor. The window is split in two:

    +-----------+--------------------------------+
    |  sidebar  |         content area           |
    | (nav)     |  one "page" per nav button     |
    +-----------+--------------------------------+

HOW THIS FILE IS ORGANISED (read the section banners as you scroll):
    1. SETTINGS          — colours, sizes, nav items. Tweak things here first.
    2. WINDOW SETUP      — __init__ / build_ui
    3. SIDEBAR           — building the nav panel
    4. SIDEBAR ANIMATION — the collapse/expand slide
    5. CONTENT PAGES     — one build_*_page() per screen
    6. PLACEHOLDER PAGE  — the "not built yet" screen
    7. PAGE ROUTING      — which page is visible
    8. USER LIST DATA    — talking to the controller

Only the "Users" page has real content right now. Every other nav item
already has its OWN build_*_page() method waiting in section 5 —
build_server_page(), build_settings_page(), build_help_page(). Each
returns the shared placeholder for now, so you can work on one screen at
a time without touching anything else.

WANT TO FILL IN AN EXISTING SCREEN? Open its build_*_page() in section 5
and replace the one placeholder line with your own widgets. Nothing else
needs changing.

WANT TO ADD A BRAND-NEW SCREEN? Three small steps:
    a) add a dict to NAV_ITEMS
    b) write a build_yourthing_page() in section 5
    c) register it in the page_builders dict inside build_content_area()
Anything you skip step (b) and (c) for automatically gets a placeholder.
"""

import time
import customtkinter as ctk
from tkinter import messagebox

from controllers.user_controller import UserController
from controllers.appointment_controller import AppointmentController
from utils.exceptions import AppointMedError
from utils.formatting import format_time

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ===========================================================================
# 1. SETTINGS — colours, nav items
# ===========================================================================

# Naming the colours means you change a shade in ONE place instead of
# hunting for the same hex code in fifteen widgets.
SIDEBAR_BG = "#1A1F2B"      # dark navy panel
SIDEBAR_HOVER = "#2A3040"   # slightly lighter, used on mouse-over
SIDEBAR_ACTIVE = "#2B6CB0"  # blue highlight on the current nav button
SIDEBAR_TEXT = "white"
AVATAR_BG = "#3A4152"       # the blank circle standing in for a photo

MUTED_TEXT = "gray50"       # subtitles / secondary info
PLACEHOLDER_TEXT = "gray30" # the big "… window" label
ERROR_TEXT = "#d64545"
SUCCESS_TEXT = "#2F855A"

DELETE_BG = "#C53030"
DELETE_HOVER = "#9B2C2C"
REFRESH_BG = "gray60"

# Role badge colours: (background, text). Used by the user list and the
# profile card.
ROLE_COLORS = {
    "doctor": ("#E3F0FF", "#2B6CB0"),
    "nurse": ("#F3E8FF", "#6B46C1"),
    "admin": ("#FBE7E7", "#C53030"),
    "pharmacist": ("#FBE7E7", "#30C549"),
}

# Appointment status badge colours: (background, text). Used by the
# clinic-wide Appointments page.
STATUS_COLORS = {
    "Scheduled": ("#EEF1F4", "#4A5568"),
    "Checked-in": ("#FFF6DC", "#B7791F"),
    "Consulting": ("#E6FFFA", "#2C7A7B"),
    "Examined": ("#E3F0FF", "#2B6CB0"),
    "Completed": ("#E3F6E8", "#2F855A"),
    "Cancelled": ("#FBE7E7", "#C53030"),
}

# NAV_ITEMS drives the whole sidebar: every button, its icon, and which
# "page" it reveals. Add/remove a dict here and the sidebar updates itself
# — you never have to touch build_sidebar() again.
#   position "top"    -> stacked from the top of the panel
#   position "bottom" -> pinned to the floor of the panel
NAV_ITEMS = [
    {"key": "users",         "icon": "👤", "label": "Users",         "position": "top"},
    {"key": "appointments",  "icon": "📅", "label": "Appointments",  "position": "top"},
    {"key": "server",        "icon": "🖥", "label": "Server",        "position": "top"},
    {"key": "settings",      "icon": "⚙",  "label": "Settings",      "position": "bottom"},
    {"key": "help",          "icon": "❓", "label": "Help",          "position": "bottom"},
]

# The profile row at the top of the sidebar is not a nav button, but it
# routes to a page just like one. This is that page's key.
PROFILE_KEY = "profile"


class AdminDashboard(ctk.CTk):
    # --- sizes you may want to tweak -------------------------------------
    WINDOW_SIZE = "1100x680"
    SIDEBAR_EXPANDED_WIDTH = 210
    SIDEBAR_COLLAPSED_WIDTH = 64
    # The animation runs for a fixed DURATION and recomputes the exact
    # width needed at each point in time (eased with ease-in-out-cubic),
    # instead of moving a constant number of pixels per tick — that's what
    # keeps it smooth instead of jerky. FRAME_MS is just how often we
    # redraw: smaller = smoother.
    ANIMATION_DURATION_S = 0.32
    ANIMATION_FRAME_MS = 8

    # ===================================================================
    # 2. WINDOW SETUP
    # ===================================================================
    def __init__(self, admin):
        super().__init__()
        self.admin = admin
        self.user_controller = UserController()
        self.appointment_controller = AppointmentController()

        # --- state the sidebar reads and writes ---
        self.sidebar_expanded = True       # is the panel currently open?
        self.current_view = "users"        # which page is on screen right now
        self.nav_buttons = {}              # key -> CTkButton, filled in below
        self.pages = {}                    # key -> page frame, filled in below

        self.title(admin.dashboard_title())
        self.geometry(self.WINDOW_SIZE)
        self.build_ui()
        self.load_users()
        self.load_appointments()

    def build_ui(self):
        """`body` is a plain container holding the sidebar on the left and
        the content area on the right, side by side."""
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

        self.build_sidebar(self.body)
        self.build_content_area(self.body)

    # ===================================================================
    # 3. SIDEBAR
    # Everything here only builds the LEFT panel. The pages it switches
    # between live further down in section 5.
    # ===================================================================
    def build_sidebar(self, parent):
        self.sidebar = ctk.CTkFrame(
            parent, width=self.SIDEBAR_EXPANDED_WIDTH,
            corner_radius=0, fg_color=SIDEBAR_BG
        )
        self.sidebar.pack(side="left", fill="y")
        # pack_propagate(False) is the key line that makes the animation
        # possible: normally a frame shrinks/grows to fit its children,
        # which would fight against us resizing it by hand. This locks the
        # frame's width to whatever we set with .configure(width=...).
        self.sidebar.pack_propagate(False)

        self.build_toggle_button()
        self.build_profile_block()
        self.build_nav_buttons()
        self.highlight_active_button()

    def build_toggle_button(self):
        """The hamburger / ✕ button that collapses and expands the panel."""
        toggle_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        toggle_row.pack(fill="x", padx=8, pady=(16, 12))

        self.toggle_btn = ctk.CTkButton(
            toggle_row, text="✕", width=36, height=36,
            fg_color="transparent", hover_color=SIDEBAR_HOVER,
            font=ctk.CTkFont(size=16),
            command=self.toggle_sidebar
        )
        self.toggle_btn.pack(side="left")

    def build_profile_block(self):
        """Avatar + name row under the hamburger. Clicking anywhere on it
        opens the profile page."""
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(fill="x", padx=8, pady=(0, 20))

        # Blank placeholder avatar: just a plain circle, no initials/photo
        # yet. Swap this out later for a real picture with something like:
        #   from PIL import Image
        #   img = ctk.CTkImage(Image.open("avatar.png"), size=(40, 40))
        #   self.profile_avatar.configure(image=img, text="")
        self.profile_avatar = ctk.CTkLabel(
            self.profile_frame, text="", width=40, height=40,
            corner_radius=20, fg_color=AVATAR_BG
        )
        self.profile_avatar.pack(side="left")

        self.profile_name_label = ctk.CTkLabel(
            self.profile_frame,
            text=getattr(self.admin, "full_name", "Admin"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=SIDEBAR_TEXT, anchor="w"
        )
        self.profile_name_label.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # CTkFrame/CTkLabel have no `command=` option like CTkButton does,
        # so we bind the raw "<Button-1>" (left click) event on each of the
        # three widgets making up the row — the frame, the avatar and the
        # name — so it doesn't matter which part gets clicked.
        for widget in (self.profile_frame, self.profile_avatar, self.profile_name_label):
            widget.bind("<Button-1>", lambda event: self.switch_view(PROFILE_KEY))
            widget.bind("<Enter>", self._on_profile_hover_enter)
            widget.bind("<Leave>", self._on_profile_hover_leave)
            # A hand cursor is the affordance a real button gives you for
            # free; set it once here rather than on every hover.
            widget.configure(cursor="hand2")

    def build_nav_buttons(self):
        """Creates one button per NAV_ITEMS entry, split into the group
        that stacks from the top and the group pinned to the bottom."""
        top_items = [item for item in NAV_ITEMS if item["position"] == "top"]
        bottom_items = [item for item in NAV_ITEMS if item["position"] == "bottom"]

        for item in top_items:
            self._make_nav_button(item).pack(fill="x", padx=8, pady=2, side="top")

        # Packing the bottom group in REVERSE with side="bottom" is what
        # pins them to the floor while keeping their on-screen order the
        # same as in NAV_ITEMS (Settings above Help): Tkinter stacks
        # side="bottom" widgets upward from the floor, so the first one
        # packed ends up lowest.
        for item in reversed(bottom_items):
            self._make_nav_button(item).pack(fill="x", padx=8, pady=2, side="bottom")

    def _make_nav_button(self, item):
        """Builds one nav button and registers it in self.nav_buttons, so
        switch_view() / highlight_active_button() / _set_sidebar_labels()
        can all find it again by key."""
        button = ctk.CTkButton(
            self.sidebar,
            text=self._nav_button_text(item, expanded=True),
            anchor="w", height=40,
            fg_color="transparent", hover_color=SIDEBAR_HOVER,
            text_color=SIDEBAR_TEXT, font=ctk.CTkFont(size=13),
            # The default-argument trick (key=item["key"]) makes each
            # lambda capture its OWN key instead of the last loop value.
            command=lambda key=item["key"]: self.switch_view(key)
        )
        self.nav_buttons[item["key"]] = button
        return button

    @staticmethod
    def _nav_button_text(item, expanded):
        """Expanded buttons read "👤   Users"; collapsed ones are icon-only."""
        if expanded:
            return f"{item['icon']}   {item['label']}"
        return item["icon"]

    def _on_profile_hover_enter(self, event=None):
        """Highlight the profile row with the same colour the nav buttons
        use, so the whole sidebar reads as one clickable family."""
        self.profile_frame.configure(fg_color=SIDEBAR_HOVER)

    def _on_profile_hover_leave(self, event=None):
        self.profile_frame.configure(fg_color="transparent")

    # ===================================================================
    # 4. SIDEBAR ANIMATION
    # ===================================================================
    def toggle_sidebar(self):
        """Called by the hamburger button. Works out the target width and
        kicks off the eased animation toward it."""
        collapsing = self.sidebar_expanded  # True if we're about to close it
        start_width = self.sidebar.winfo_width()
        target_width = self.SIDEBAR_COLLAPSED_WIDTH if collapsing else self.SIDEBAR_EXPANDED_WIDTH
        self.sidebar_expanded = not self.sidebar_expanded

        # Morph the hamburger into an ✕ (and back) the instant the click
        # happens — it's a fixed-width button so there's no squish risk,
        # and reacting immediately makes the toggle feel responsive even
        # though the panel itself takes a moment to glide.
        self.toggle_btn.configure(text="✕" if self.sidebar_expanded else "☰")

        if collapsing:
            # Shorten the labels RIGHT NOW, before the frame starts
            # shrinking, so text never gets squeezed or clipped mid-slide.
            # When expanding we do the opposite and wait until the panel
            # is fully open — see the end of _animate_sidebar().
            self._set_sidebar_labels(expanded=False)

        self._animate_sidebar(
            start_width=start_width,
            target_width=target_width,
            start_time=time.perf_counter(),
            collapsing=collapsing,
        )

    def _animate_sidebar(self, start_width, target_width, start_time, collapsing):
        """Runs every ANIMATION_FRAME_MS milliseconds for a fixed total
        duration. Rather than moving a constant number of pixels each tick,
        we look at how much time has actually elapsed and compute exactly
        where the sidebar should be *right now* on an ease-in-out curve.
        That keeps the motion identical no matter how fast the machine
        renders each frame."""
        elapsed = time.perf_counter() - start_time
        progress = min(elapsed / self.ANIMATION_DURATION_S, 1.0)  # 0.0 -> 1.0
        eased = self.ease_in_out_cubic(progress)

        new_width = round(start_width + (target_width - start_width) * eased)
        self.sidebar.configure(width=new_width)

        if progress < 1.0:
            self.after(
                self.ANIMATION_FRAME_MS,
                lambda: self._animate_sidebar(start_width, target_width, start_time, collapsing)
            )
            return

        # Finished: snap exactly onto the target width so rounding can't
        # leave us 1px off, then reveal the full labels again if we were
        # expanding.
        self.sidebar.configure(width=target_width)
        if not collapsing:
            self._set_sidebar_labels(expanded=True)

    @staticmethod
    def ease_in_out_cubic(t):
        """A symmetric 'ease-in-out' curve: gentle acceleration off the
        start, gentle deceleration into the stop, instead of a constant
        speed the whole way. This is the curve most smooth UI sidebar
        animations use."""
        if t < 0.5:
            return 4 * t ** 3
        return 1 - ((-2 * t + 2) ** 3) / 2

    def _set_sidebar_labels(self, expanded):
        """Collapsed: icon-only buttons and no name next to the avatar, so
        nothing gets clipped. Expanded: full labels come back."""
        for item in NAV_ITEMS:
            button = self.nav_buttons[item["key"]]
            button.configure(
                text=self._nav_button_text(item, expanded),
                anchor="w" if expanded else "center"
            )

        if expanded:
            self.profile_name_label.pack(side="left", padx=(10, 0), fill="x", expand=True)
        else:
            self.profile_name_label.pack_forget()

    # ===================================================================
    # 5. CONTENT PAGES
    # Each build_*_page() returns ONE frame. They're all stacked on top of
    # each other and raised as needed (see section 7).
    # ===================================================================
    def build_content_area(self, parent):
        self.content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True)

        # PAGE_BUILDERS maps a nav key to the method that builds its real
        # screen. Any key NOT listed here falls back to a placeholder, so
        # a new NAV_ITEMS entry works immediately without extra code.
        page_builders = {
            "users":         self.build_users_page,
            "appointments":  self.build_appointments_page,
            "server":        self.build_server_page,
            "settings":      self.build_settings_page,
            "help":          self.build_help_page,
        }

        for item in NAV_ITEMS:
            key = item["key"]
            if key in page_builders:
                self.pages[key] = page_builders[key](self.content_frame)
            else:
                self.pages[key] = self.build_placeholder_page(
                    self.content_frame, f"{item['label']} window"
                )

        # "profile" isn't a sidebar nav button (it's not in NAV_ITEMS), but
        # it's routed to in exactly the same way — it's just one more entry
        # in this dict, raised when the profile row is clicked.
        self.pages[PROFILE_KEY] = self.build_profile_page(self.content_frame)

        # place() with relwidth/relheight 1 stacks every page full-size on
        # top of the others; lift() then picks the visible one.
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.current_view)

    def build_users_page(self, parent):
        """The main screen: header row + scrollable list of accounts."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text=self.admin.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ Add user", width=120, command=self.open_add_form
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color=REFRESH_BG,
            command=self.load_users
        ).pack(side="right")

        ctk.CTkLabel(
            page, text="User accounts", font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # load_users() empties and refills this frame; it must exist before
        # load_users() is called in __init__.
        self.list_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def build_appointments_page(self, parent):
        """Read-only, clinic-wide view of every appointment. Admins aren't
        part of the booking workflow (that's the nurse's and doctor's
        job — see schema.sql), but an admin's "view_all_records"
        permission means they should still be able to see everything
        that's scheduled across every doctor, in one place."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            header, text="Appointments",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color=REFRESH_BG,
            command=self.load_appointments
        ).pack(side="right")

        ctk.CTkLabel(
            page, text="Every appointment across the clinic, most recent first.",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # load_appointments() empties and refills this frame; it must
        # exist before load_appointments() is called in __init__.
        self.appointments_list_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.appointments_list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def build_profile_page(self, parent):
        """"My Account" — shown in the same spot as the other pages when
        the admin clicks their avatar/name in the sidebar. Has a summary
        card at the top, then two small forms: one to edit their name,
        one to change the password. Both talk to UserController, which
        is where the actual validation and the UPDATE statements live."""
        # A scrollable frame instead of a plain one so the page can grow
        # past the visible window height (e.g. once both edit forms are
        # opened) without anything getting cut off.
        page = ctk.CTkScrollableFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            header, text="My Account",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            page, text="Account details", font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # --- summary card: avatar, name, username, role badge ----------
        card = ctk.CTkFrame(page, corner_radius=10)
        card.pack(fill="x", padx=24)

        avatar_row = ctk.CTkFrame(card, fg_color="transparent")
        avatar_row.pack(fill="x", padx=20, pady=20)

        # Big blank avatar circle, same placeholder idea as the sidebar one.
        ctk.CTkLabel(
            avatar_row, text="", width=64, height=64, corner_radius=32,
            fg_color=AVATAR_BG
        ).pack(side="left")

        text_col = ctk.CTkFrame(avatar_row, fg_color="transparent")
        text_col.pack(side="left", padx=(16, 0), fill="x", expand=True)

        # Stored on self so save_profile_details() can update this text in
        # place after a successful save, instead of rebuilding the page.
        self.profile_page_name_label = ctk.CTkLabel(
            text_col, text=getattr(self.admin, "full_name", "Admin"),
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self.profile_page_name_label.pack(fill="x")
        ctk.CTkLabel(
            text_col, text="@" + getattr(self.admin, "username", "admin"),
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x", pady=(2, 0))

        badge_bg, badge_fg = ROLE_COLORS["admin"]
        ctk.CTkLabel(
            text_col, text="Administrator",
            fg_color=badge_bg, text_color=badge_fg,
            corner_radius=8, font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(8, 0), ipadx=8, ipady=2)

        ctk.CTkFrame(card, fg_color="transparent", height=4).pack(fill="x")

        # --- edit details form -------------------------------------------
        details_card = ctk.CTkFrame(page, corner_radius=10)
        details_card.pack(fill="x", padx=24, pady=(16, 0))

        details_header = ctk.CTkFrame(details_card, fg_color="transparent")
        details_header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            details_header, text="Edit details", font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).pack(side="left")
        self.details_edit_btn = ctk.CTkButton(
            details_header, text="Edit", width=70, height=26,
            fg_color=REFRESH_BG, command=self.toggle_details_edit
        )
        self.details_edit_btn.pack(side="right")

        # Everything below is the actual editable form. It's built here but
        # NOT packed yet — it only appears once "Edit" is pressed, via
        # toggle_details_edit().
        self.details_form = ctk.CTkFrame(details_card, fg_color="transparent")

        ctk.CTkLabel(self.details_form, text="Full name", anchor="w").pack(fill="x", padx=20)
        self.profile_fullname_entry = ctk.CTkEntry(self.details_form, width=300)
        self.profile_fullname_entry.insert(0, getattr(self.admin, "full_name", ""))
        self.profile_fullname_entry.pack(anchor="w", padx=20, pady=(2, 6))

        self.profile_details_status = ctk.CTkLabel(self.details_form, text="", text_color=ERROR_TEXT)
        self.profile_details_status.pack(anchor="w", padx=20)

        ctk.CTkButton(
            self.details_form, text="Save changes", width=140, command=self.save_profile_details
        ).pack(anchor="w", padx=20, pady=(10, 20))

        # --- change password form ----------------------------------------
        password_card = ctk.CTkFrame(page, corner_radius=10)
        password_card.pack(fill="x", padx=24, pady=(16, 20))

        password_header = ctk.CTkFrame(password_card, fg_color="transparent")
        password_header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            password_header, text="Change password", font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).pack(side="left")
        self.password_edit_btn = ctk.CTkButton(
            password_header, text="Edit", width=70, height=26,
            fg_color=REFRESH_BG, command=self.toggle_password_edit
        )
        self.password_edit_btn.pack(side="right")

        # Hidden until "Edit" is pressed, same as details_form above.
        self.password_form = ctk.CTkFrame(password_card, fg_color="transparent")

        self.current_password_entry = ctk.CTkEntry(
            self.password_form, width=300, show="*", placeholder_text="Current password"
        )
        self.current_password_entry.pack(anchor="w", padx=20, pady=(0, 6))

        self.new_password_entry = ctk.CTkEntry(
            self.password_form, width=300, show="*", placeholder_text="New password"
        )
        self.new_password_entry.pack(anchor="w", padx=20, pady=(0, 6))

        self.confirm_password_entry = ctk.CTkEntry(
            self.password_form, width=300, show="*", placeholder_text="Confirm new password"
        )
        self.confirm_password_entry.pack(anchor="w", padx=20, pady=(0, 6))

        self.profile_password_status = ctk.CTkLabel(self.password_form, text="", text_color=ERROR_TEXT)
        self.profile_password_status.pack(anchor="w", padx=20)

        ctk.CTkButton(
            self.password_form, text="Update password", width=140, command=self.save_profile_password
        ).pack(anchor="w", padx=20, pady=(10, 20))

        return page

    def toggle_details_edit(self):
        """Shows/hides the "Edit details" form. The button doubles as
        Edit/Cancel depending on whether the form is currently open."""
        if self.details_form.winfo_ismapped():
            self.details_form.pack_forget()
            self.details_edit_btn.configure(text="Edit")
        else:
            self.details_form.pack(fill="x")
            self.details_edit_btn.configure(text="Cancel")

    def toggle_password_edit(self):
        """Shows/hides the "Change password" form, same Edit/Cancel pattern
        as toggle_details_edit()."""
        if self.password_form.winfo_ismapped():
            self.password_form.pack_forget()
            self.password_edit_btn.configure(text="Edit")
        else:
            self.password_form.pack(fill="x")
            self.password_edit_btn.configure(text="Cancel")

    def save_profile_details(self):
        """Handles the "Save changes" button on the details form."""
        full_name = self.profile_fullname_entry.get().strip()

        try:
            self.user_controller.update_details(self.admin.user_id, full_name)
        except AppointMedError as e:
            self.profile_details_status.configure(text_color=ERROR_TEXT, text=str(e))
            return

        # Reflect the change immediately, everywhere the name shows up,
        # without needing to log out and back in.
        self.admin.full_name = full_name
        self.profile_page_name_label.configure(text=full_name)
        self.profile_name_label.configure(text=full_name)
        self.title(self.admin.dashboard_title())
        self.profile_details_status.configure(text_color=SUCCESS_TEXT, text="Saved.")

    def save_profile_password(self):
        """Handles the "Update password" button on the password form."""
        current = self.current_password_entry.get().strip()
        new = self.new_password_entry.get().strip()
        confirm = self.confirm_password_entry.get().strip()

        try:
            self.user_controller.change_password(self.admin.user_id, current, new, confirm)
        except AppointMedError as e:
            self.profile_password_status.configure(text_color=ERROR_TEXT, text=str(e))
            return

        self.current_password_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        self.confirm_password_entry.delete(0, "end")
        self.profile_password_status.configure(text_color=SUCCESS_TEXT, text="Password updated.")

    # -------------------------------------------------------------------
    # SCREENS STILL TO BE BUILT
    # Each one already has its own method, is already registered in
    # page_builders, and is already wired to its sidebar button — it just
    # returns the shared placeholder for now, so the app looks exactly as
    # it does today.
    #
    # To start building one: delete the placeholder line and build the
    # frame yourself. The pattern is the same as build_users_page() above:
    #
    #     def build_server_page(self, parent):
    #         page = ctk.CTkFrame(parent, fg_color="transparent")
    #         ctk.CTkLabel(page, text="Server").pack(padx=24, pady=20)
    #         ... add the rest of your widgets to `page` ...
    #         return page          # <- always return the frame
    #
    # Two rules to remember:
    #   * `parent` must be the parent of every widget you create here.
    #   * return the frame; build_content_area() places it for you.
    # If a screen needs to load data, put the loading in its own method
    # (like load_users()) and call it after the window is built, not
    # inside the builder.
    # -------------------------------------------------------------------
    def build_server_page(self, parent):
        """Server tab — database host/connection status. Not built yet."""
        return self.build_placeholder_page(parent, "Server window")

    def build_settings_page(self, parent):
        """Settings tab — app-wide preferences. Not built yet."""
        return self.build_placeholder_page(parent, "Settings window")

    def build_help_page(self, parent):
        """Help tab — usage guide / support contact. Not built yet."""
        return self.build_placeholder_page(parent, "Help window")

    # ===================================================================
    # 6. PLACEHOLDER PAGE
    # Deliberately kept on its own: it is NOT sidebar code and NOT a real
    # screen — it's the stand-in that the unfinished build_*_page() methods
    # in section 5 return, plus the fallback for any nav key that has no
    # builder registered at all.
    # ===================================================================
    def build_placeholder_page(self, parent, text):
        """A big centred label confirming which button was pressed. You
        don't call this directly when building a real screen — you stop
        calling it, and build the frame in that screen's own method."""
        page = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(
            page, text=text, font=ctk.CTkFont(size=24, weight="bold"),
            text_color=PLACEHOLDER_TEXT
        ).pack(expand=True)
        return page

    # ===================================================================
    # 7. PAGE ROUTING
    # ===================================================================
    def switch_view(self, key):
        """Wired to every nav button's command= and to the profile row.
        Records the new page, shows it, and re-highlights the sidebar."""
        self.current_view = key
        self.show_page(key)
        self.highlight_active_button()

    def show_page(self, key):
        """Bring one stacked page to the front.

        Use lift(), NOT tkraise(). They are the same method on a normal
        widget, but a CTkScrollableFrame (which the profile page is, so
        it can scroll) is really two frames: an outer one that gets
        placed, and the inner one you add widgets to. CustomTkinter
        redirects lift() to that outer frame but leaves tkraise() on the
        inner one - so tkraise() here raised a frame that isn't part of
        the page stack at all, and clicking the profile row appeared to
        do nothing."""
        self.pages[key].lift()

    def highlight_active_button(self):
        """Blue background on the current page's button, transparent on the
        rest. Clicking the profile row matches no key, so every button goes
        transparent — which is what we want."""
        for key, button in self.nav_buttons.items():
            is_active = (key == self.current_view)
            button.configure(fg_color=SIDEBAR_ACTIVE if is_active else "transparent")

    # ===================================================================
    # 8. USER LIST DATA
    # Everything below talks to UserController; no layout decisions here
    # beyond drawing one row per account.
    # ===================================================================
    def clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def load_users(self):
        """Redraw the whole list from scratch. Called on start-up, after
        Refresh, and after any add/delete."""
        self.clear_list()
        try:
            users = self.user_controller.get_all_users()
        except AppointMedError:
            users = []

        if not users:
            ctk.CTkLabel(
                self.list_frame, text="No users found.", text_color=MUTED_TEXT
            ).pack(pady=40)
            return

        for user in users:
            self.add_user_row(user)

    def add_user_row(self, user):
        row = ctk.CTkFrame(self.list_frame, corner_radius=10)
        row.pack(fill="x", pady=5)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        ctk.CTkLabel(
            info, text=user["full_name"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            info, text=self.user_subtitle(user),
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x")

        badge_bg, badge_fg = ROLE_COLORS.get(user["role"], ROLE_COLORS["admin"])
        ctk.CTkLabel(
            row, text=user["role"].capitalize(), fg_color=badge_bg, text_color=badge_fg,
            corner_radius=8, width=80, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        ctk.CTkButton(
            row, text="Delete", width=70, height=26,
            fg_color=DELETE_BG, hover_color=DELETE_HOVER,
            # default-argument trick again, so each row's button remembers
            # its own user
            command=lambda u=user: self.delete_user(u)
        ).pack(side="right", padx=(8, 0))

    @staticmethod
    def user_subtitle(user):
        """Second line of a row: "@jdoe · Pediatrics" or
        "@jdoe · assigned to doctor #3"."""
        subtitle = "@" + user["username"]
        if user["role"] == "doctor" and user.get("specialization"):
            subtitle = subtitle + " · " + user["specialization"]
        if user["role"] == "nurse" and user.get("assigned_doctor_id"):
            subtitle = subtitle + " · assigned to doctor #" + str(user["assigned_doctor_id"])
        return subtitle

    def delete_user(self, user):
        confirmed = messagebox.askyesno("Confirm", "Delete account for " + user["full_name"] + "?")
        if not confirmed:
            return
        try:
            self.user_controller.delete_user(user["id"])
        except AppointMedError as e:
            messagebox.showerror("Error", str(e))
        self.load_users()

    # ===================================================================
    # 9. APPOINTMENT LIST DATA
    # Everything below talks to AppointmentController for the read-only,
    # clinic-wide Appointments page; no layout decisions here beyond
    # drawing one row per appointment.
    # ===================================================================
    def clear_appointments_list(self):
        for widget in self.appointments_list_frame.winfo_children():
            widget.destroy()

    def load_appointments(self):
        """Redraw the whole appointment list from scratch. Called on
        start-up and after Refresh."""
        self.clear_appointments_list()
        try:
            appointments = self.appointment_controller.get_all_appointments()
        except AppointMedError:
            appointments = []

        if not appointments:
            ctk.CTkLabel(
                self.appointments_list_frame, text="No appointments found.", text_color=MUTED_TEXT
            ).pack(pady=40)
            return

        for appt in appointments:
            self.add_appointment_row(appt)

    def add_appointment_row(self, appt):
        """One row: appointee name + doctor/nurse/time on a second line,
        plus a status badge. Read-only - an admin can see the whole
        clinic's schedule here, but booking and status changes stay with
        the nurse and doctor who actually run that appointment."""
        row = ctk.CTkFrame(self.appointments_list_frame, corner_radius=10)
        row.pack(fill="x", pady=5)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        ctk.CTkLabel(
            info, text=appt["full_name"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")

        when = appt["scheduled_time"].strftime("%b %d, %Y — ") + format_time(appt["scheduled_time"])
        subtitle = when + " · Dr. " + appt["doctor_name"] + " · Nurse " + appt["nurse_name"]
        ctk.CTkLabel(
            info, text=subtitle, font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x")

        badge_bg, badge_fg = STATUS_COLORS.get(appt["status"], STATUS_COLORS["Scheduled"])
        ctk.CTkLabel(
            row, text=appt["status"], fg_color=badge_bg, text_color=badge_fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=16)

    # ------------------------------------------------------------------
    # ADD-USER FORM (a small pop-up window)
    # ------------------------------------------------------------------
    def open_add_form(self):
        form = ctk.CTkToplevel(self)
        form.title("Add User")
        form.geometry("380x560")
        form.grab_set()  # modal: blocks clicks on the dashboard behind it

        ctk.CTkLabel(
            form, text="New User Account", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 16))

        username_entry = self.labeled_entry(form, "Username")
        password_entry = self.labeled_entry(form, "Password", show="*")
        full_name_entry = self.labeled_entry(form, "Full name")

        ctk.CTkLabel(form, text="Role", anchor="w").pack(fill="x", padx=30, pady=(10, 2))
        role_var = ctk.StringVar(value="doctor")
        role_menu = ctk.CTkOptionMenu(form, values=["doctor", "nurse", "admin"], variable=role_var)
        role_menu.pack(padx=30, fill="x")

        specialization_entry = self.labeled_entry(form, "Specialization (doctors only)")
        doctor_id_entry = self.labeled_entry(form, "Assigned doctor ID (nurses only)")

        status_label = ctk.CTkLabel(form, text="", text_color=ERROR_TEXT)
        status_label.pack(pady=(4, 0))

        # Defined inside open_add_form() so it can read the entry widgets
        # above directly, without storing them on self.
        def submit():
            try:
                role = role_var.get()

                # These two fields only apply to one role each.
                specialization = None
                if role == "doctor":
                    specialization = specialization_entry.get().strip() or None

                assigned_doctor_id = None
                if role == "nurse" and doctor_id_entry.get().strip():
                    assigned_doctor_id = int(doctor_id_entry.get())

                self.user_controller.add_user(
                    username=username_entry.get().strip(),
                    password=password_entry.get().strip(),
                    full_name=full_name_entry.get().strip(),
                    role=role,
                    specialization=specialization,
                    assigned_doctor_id=assigned_doctor_id,
                )
                form.destroy()
                self.load_users()
            except AppointMedError as e:
                # Business-rule problems (duplicate username, etc.)
                status_label.configure(text=str(e))
            except ValueError:
                # int() failed on the doctor ID
                status_label.configure(text="Assigned doctor ID must be a number.")

        ctk.CTkButton(form, text="Create account", command=submit).pack(pady=24)

    @staticmethod
    def labeled_entry(parent, label_text, show=None):
        """Label above an entry box — the pattern every form field uses.
        Pass show="*" to mask the text for passwords."""
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(fill="x", padx=30, pady=(10, 2))
        if show:
            entry = ctk.CTkEntry(parent, width=300, show=show)
        else:
            entry = ctk.CTkEntry(parent, width=300)
        entry.pack(padx=30)
        return entry
