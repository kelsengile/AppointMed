"""
Doctor's dashboard — built with CustomTkinter.

Same two-part layout as the other dashboards:

    +-----------+--------------------------------+
    |  sidebar  |         content area           |
    | (nav)     |  one "page" per nav button     |
    +-----------+--------------------------------+

Only the "Appointments" page has real content right now (today's schedule
as cards with a status badge and a "Complete" button). Every other nav
item already has its OWN build_*_page() method waiting in section 5 —
build_doctor_page(), build_room_page(), build_notifications_page(),
build_invoice_page(), build_history_page(), build_settings_page(),
build_help_page(). Each returns the shared placeholder for now, so you
can work on one screen at a time without touching anything else.

HOW THIS FILE IS ORGANISED (read the section banners as you scroll):
    1. SETTINGS           — colours, sizes, nav items. Tweak things here first.
    2. WINDOW SETUP       — __init__ / build_ui
    3. SIDEBAR            — building the nav panel
    4. SIDEBAR ANIMATION  — the collapse/expand slide
    5. CONTENT PAGES      — one build_*_page() per screen
    6. PLACEHOLDER PAGE   — the "not built yet" screen
    7. PAGE ROUTING       — which page is visible
    8. APPOINTMENT DATA   — talking to the controller

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
from datetime import date

from controllers.appointment_controller import AppointmentController
from utils.exceptions import AppointMedError

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

COMPLETE_BG = "#2F855A"
COMPLETE_HOVER = "#276749"

DOCTOR_BADGE_BG = "#E3F0FF"
DOCTOR_BADGE_FG = "#2B6CB0"

# Appointment status badge colours: (background, text).
STATUS_COLORS = {
    "Scheduled": ("#EEF1F4", "#4A5568"),
    "Checked-in": ("#FFF6DC", "#B7791F"),
    "Completed": ("#E3F6E8", "#2F855A"),
    "Cancelled": ("#FBE7E7", "#C53030"),
}

# Statuses that are already finished, so no action button is drawn.
FINISHED_STATUSES = ("Completed", "Cancelled")

# NAV_ITEMS drives the whole sidebar: every button, its icon, and where it
# sits. Add/remove a dict here and the sidebar updates itself — you never
# have to touch build_sidebar() again.
#   position "top" / "middle" -> stacked from the top, in list order
#   position "bottom"         -> pinned to the floor of the panel
NAV_ITEMS = [
    {"key": "appointments",  "icon": "📅",         "label": "Appointments",  "position": "top"},
    {"key": "doctor",        "icon": "👨🏻",       "label": "Doctor",        "position": "top"},
    {"key": "room",          "icon": "🔑",         "label": "Room",          "position": "top"},
    {"key": "notifications", "icon": "🔔",         "label": "Notifications", "position": "middle"},
    {"key": "invoice",       "icon": "🧾",         "label": "Invoice",       "position": "middle"},
    {"key": "history",       "icon": "🧾",         "label": "History",       "position": "middle"},
    {"key": "settings",      "icon": "⚙",          "label": "Settings",      "position": "bottom"},
    {"key": "help",          "icon": "❓",         "label": "Help",          "position": "bottom"},
]

# Positions that stack from the top of the panel.
STACKED_POSITIONS = ("top", "middle")

# The profile row at the top of the sidebar is not a nav button, but it
# routes to a page just like one. This is that page's key.
PROFILE_KEY = "profile"


class DoctorDashboard(ctk.CTk):
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
    def __init__(self, doctor):
        super().__init__()
        self.doctor = doctor
        self.appointment_controller = AppointmentController()

        # --- state the sidebar reads and writes ---
        self.sidebar_expanded = True         # is the panel currently open?
        self.current_view = "appointments"   # which page is on screen right now
        self.nav_buttons = {}                # key -> CTkButton, filled in below
        self.pages = {}                      # key -> page frame, filled in below

        self.title(doctor.dashboard_title())
        self.geometry(self.WINDOW_SIZE)
        self.build_ui()
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

        # Plain circle, no photo yet. Swap in a real picture later with:
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
            text=getattr(self.doctor, "full_name", "Doctor"),
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
        stacked_items = [i for i in NAV_ITEMS if i["position"] in STACKED_POSITIONS]
        bottom_items = [i for i in NAV_ITEMS if i["position"] == "bottom"]

        for item in stacked_items:
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
        """Expanded buttons read "📅   Appointments"; collapsed ones are
        icon-only."""
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

        # page_builders maps a nav key to the method that builds its real
        # screen. Any key NOT listed here falls back to a placeholder, so
        # a new NAV_ITEMS entry works immediately without extra code.
        page_builders = {
            "appointments":  self.build_appointments_page,
            "doctor":        self.build_doctor_page,
            "room":          self.build_room_page,
            "notifications": self.build_notifications_page,
            "invoice":       self.build_invoice_page,
            "history":       self.build_history_page,
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
        # top of the others; tkraise() then picks the visible one.
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.current_view)

    def build_appointments_page(self, parent):
        """The main screen: header row + today's schedule."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        ctk.CTkLabel(
            header, text=self.doctor.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=90, command=self.load_appointments
        ).pack(side="right")

        ctk.CTkLabel(
            page, text="Today — " + date.today().strftime("%A, %B %d"),
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # load_appointments() empties and refills this frame; it must exist
        # before load_appointments() is called in __init__.
        self.list_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def build_profile_page(self, parent):
        """"My Account" — shown in the same spot as the other pages when
        the doctor clicks their avatar/name in the sidebar. Replace the
        read-only fields below with real edit-profile widgets whenever
        you're ready."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            header, text="My Account",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            page, text="Account details", font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 16))

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

        ctk.CTkLabel(
            text_col, text=getattr(self.doctor, "full_name", "Doctor"),
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            text_col, text="@" + getattr(self.doctor, "username", "doctor"),
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(
            text_col, text="Doctor",
            fg_color=DOCTOR_BADGE_BG, text_color=DOCTOR_BADGE_FG,
            corner_radius=8, font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(8, 0), ipadx=8, ipady=2)

        specialization = getattr(self.doctor, "specialization", None)
        if specialization:
            ctk.CTkLabel(
                card, text="Specialization: " + specialization,
                font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
            ).pack(fill="x", padx=20, pady=(0, 20))
        else:
            # An invisible 4px strip, so the card's bottom edge sits in the
            # same place whether or not there's a specialization to show.
            ctk.CTkFrame(card, fg_color="transparent", height=4).pack(fill="x")

        return page

    # -------------------------------------------------------------------
    # SCREENS STILL TO BE BUILT
    # Each one already has its own method, is already registered in
    # page_builders, and is already wired to its sidebar button — it just
    # returns the shared placeholder for now, so the app looks exactly as
    # it does today.
    #
    # To start building one: delete the placeholder line and build the
    # frame yourself. The pattern is the same as build_appointments_page()
    # above:
    #
    #     def build_room_page(self, parent):
    #         page = ctk.CTkFrame(parent, fg_color="transparent")
    #         ctk.CTkLabel(page, text="Rooms").pack(padx=24, pady=20)
    #         ... add the rest of your widgets to `page` ...
    #         return page          # <- always return the frame
    #
    # Two rules to remember:
    #   * `parent` must be the parent of every widget you create here.
    #   * return the frame; build_content_area() places it for you.
    # If a screen needs to load data, put the loading in its own method
    # (like load_appointments()) and call it after the window is built,
    # not inside the builder.
    # -------------------------------------------------------------------
    def build_doctor_page(self, parent):
        """Doctor tab — the doctor's own details/profile. Not built yet."""
        return self.build_placeholder_page(parent, "Doctor window")

    def build_room_page(self, parent):
        """Room tab — consultation room assignment/status. Not built yet."""
        return self.build_placeholder_page(parent, "Room window")

    def build_notifications_page(self, parent):
        """Notifications tab — alerts and reminders. Not built yet."""
        return self.build_placeholder_page(parent, "Notifications window")

    def build_invoice_page(self, parent):
        """Invoice tab — billing for completed visits. Not built yet."""
        return self.build_placeholder_page(parent, "Invoice window")

    def build_history_page(self, parent):
        """History tab — past appointments beyond today. Not built yet."""
        return self.build_placeholder_page(parent, "History window")

    def build_settings_page(self, parent):
        """Settings tab — preferences for this account. Not built yet."""
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
        """Bring one stacked page to the front."""
        self.pages[key].tkraise()

    def highlight_active_button(self):
        """Blue background on the current page's button, transparent on the
        rest. Clicking the profile row matches no key, so every button goes
        transparent — which is what we want."""
        for key, button in self.nav_buttons.items():
            is_active = (key == self.current_view)
            button.configure(fg_color=SIDEBAR_ACTIVE if is_active else "transparent")

    # ===================================================================
    # 8. APPOINTMENT DATA
    # Everything below talks to AppointmentController; no layout decisions
    # here beyond drawing one card per appointment.
    # ===================================================================
    def clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def load_appointments(self):
        """Redraw the whole schedule from scratch. Called on start-up,
        after Refresh, and after an appointment is completed."""
        self.clear_list()
        appointments = self.fetch_todays_appointments()

        if not appointments:
            ctk.CTkLabel(
                self.list_frame, text="No appointments scheduled for today.",
                text_color=MUTED_TEXT
            ).pack(pady=40)
            return

        for appt in appointments:
            self.add_appointment_card(appt)

    def fetch_todays_appointments(self):
        """Ask the controller for today's rows and flatten them into plain
        dicts the UI can read. Returns [] if anything goes wrong, so a
        database hiccup shows an empty schedule instead of crashing."""
        try:
            rows = self.appointment_controller.get_schedule_for_doctor(
                self.doctor.user_id, date.today().isoformat()
            )
        except AppointMedError:
            return []

        appointments = []
        for row in rows:
            record = dict(row)
            # Fall back to an ID if the join didn't give us a name.
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
        return appointments

    def add_appointment_card(self, appt):
        """One row: time | patient + reason | status badge | action."""
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
            info, text=appt["reason"], font=ctk.CTkFont(size=12),
            text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x")

        badge_bg, badge_fg = STATUS_COLORS.get(appt["status"], STATUS_COLORS["Scheduled"])
        ctk.CTkLabel(
            card, text=appt["status"], fg_color=badge_bg, text_color=badge_fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        # Nothing left to do on an appointment that's already finished.
        if appt["status"] not in FINISHED_STATUSES:
            ctk.CTkButton(
                card, text="Complete", width=80, height=26,
                fg_color=COMPLETE_BG, hover_color=COMPLETE_HOVER,
                # default-argument trick again, so each card's button
                # remembers its own appointment
                command=lambda a=appt: self.mark_completed(a)
            ).pack(side="right", padx=(8, 0))

    def mark_completed(self, appt):
        try:
            self.appointment_controller.update_status(appt["id"], "Completed")
        except AppointMedError:
            pass  # reloading below will show the unchanged status
        self.load_appointments()


# Lets you run this file on its own (python -m views.doctor.doctor_dashboard)
# with a fake doctor, instead of logging in every time you tweak the layout.
if __name__ == "__main__":
    class FakeDoctor:
        user_id = 1
        full_name = "Dr. Juan Diaz"

        def dashboard_title(self):
            return "Dr. Juan Diaz — Pediatrics"

    DoctorDashboard(FakeDoctor()).mainloop()
