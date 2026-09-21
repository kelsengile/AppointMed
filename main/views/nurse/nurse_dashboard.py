"""
Nurse/Secretary dashboard — built with CustomTkinter.

Shows and manages the schedule of the ONE doctor this nurse is assigned to
(nurse.assigned_doctor_id). Same two-part layout and the same nav items as
the doctor dashboard, so both roles feel like the same app:

    +-----------+--------------------------------+
    |  sidebar  |         content area           |
    | (nav)     |  one "page" per nav button     |
    +-----------+--------------------------------+

Two pages have real content right now:
  * "Appointments" - the NURSE'S OWN appointment board (see section 1B):
    a read-only Consulting Now box, the waiting queue (no buttons - once
    a patient is checked in only the doctor moves them on), then the
    still-scheduled appointments grouped by day with Check in / Cancel
    buttons, and a month filter on the right.
  * "History" - every appointment that has been Completed or Cancelled.
The board code now lives in THIS file (it is no longer shared with the
doctor dashboard), so you can change the nurse's board freely without
affecting the doctor's. Every other nav item already has its OWN
build_*_page() method waiting in section 5 — build_doctor_page(),
build_room_page(), build_notifications_page(), build_invoice_page(),
build_settings_page(), build_help_page(). Each returns the shared
placeholder for now.

HOW THIS FILE IS ORGANISED (read the section banners as you scroll):
    1. SETTINGS           — colours, sizes, nav items. Tweak things here first.
    1A. BOARD HELPERS     — small functions/classes the boards use
    1B. APPOINTMENT BOARD — the nurse's Appointments page body
    1C. HISTORY BOARD     — the nurse's History page body
    2. WINDOW SETUP       — __init__ / build_ui
    3. SIDEBAR            — building the nav panel
    4. SIDEBAR ANIMATION  — the collapse/expand slide
    5. CONTENT PAGES      — one build_*_page() per screen
    6. PLACEHOLDER PAGE   — the "not built yet" screen
    7. PAGE ROUTING       — which page is visible
    8. APPOINTMENT DATA   — telling the boards when to refresh, add form

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
from datetime import date, datetime, timedelta

from controllers.appointment_controller import AppointmentController
from controllers.user_controller import UserController
from utils.exceptions import AppointMedError
from utils.avatar import render_avatar
from utils.formatting import format_datetime, format_time

from views.shared.profile_page import ProfilePage

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

REFRESH_BG = "gray60"

NURSE_BADGE_BG = "#F3E8FF"
NURSE_BADGE_FG = "#6B46C1"

# --- appointment board colours (nurse's board) ----------------------------
DIVIDER_COLOR = "gray75"

CHECKIN_BG = "#2B6CB0"
CHECKIN_HOVER = "#2C5282"
CANCEL_BG = "#C53030"
CANCEL_HOVER = "#9B2C2C"
NAV_BTN_BG = "gray60"

QUEUE_BG = "#FFF9E6"
QUEUE_BORDER = "#F0D98C"
QUEUE_TEXT = "#B7791F"

CONSULT_BOX_BG = "#E6FFFA"
CONSULT_BOX_BORDER = "#81E6D9"
CONSULT_BOX_TEXT = "#2C7A7B"

# True  -> whoever checked in EARLIEST is at the top of the queue (they are
#          served first: first in, first served).
# False -> the most recent check-in is at the top instead.
QUEUE_EARLIEST_FIRST = True

# History badge colours: (background, text).
STATUS_COLORS = {
    "Completed": ("#E3F6E8", "#2F855A"),
    "Cancelled": ("#FBE7E7", "#C53030"),
}

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


# ===========================================================================
# 1A. BOARD HELPERS
# Small pieces the nurse's boards below are built from.
# ===========================================================================
def add_months(year, month, delta):
    """(year, month) moved forward/back by `delta` months."""
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def month_title(year, month):
    return date(year, month, 1).strftime("%B %Y")


def day_label(day):
    """"Today"/"Tomorrow" for the two days a clinic cares about most, the
    plain date for everything else."""
    today = date.today()
    if day == today:
        return "TODAY — " + day.strftime("%A, %B %d").upper()
    if day == today + timedelta(days=1):
        return "TOMORROW — " + day.strftime("%A, %B %d").upper()
    return day.strftime("%A, %B %d").upper()


def _scroll_canvas(scrollable):
    """The canvas inside a CTkScrollableFrame, or None if a future
    CustomTkinter release renames it (we then just skip scroll-keeping)."""
    return getattr(scrollable, "_parent_canvas", None)


class _ScrollList(ctk.CTkScrollableFrame):
    """A scrollable list that can redraw itself without jumping back to the
    top. Rebuilding a long month would otherwise throw the reader away
    from wherever they had scrolled to."""

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def scroll_position(self):
        canvas = _scroll_canvas(self)
        return canvas.yview()[0] if canvas is not None else 0.0

    def restore_scroll(self, position):
        canvas = _scroll_canvas(self)
        if canvas is None:
            return
        # Let the freshly built widgets be measured first, otherwise the
        # scrollregion is still the old one and the jump goes nowhere.
        self.update_idletasks()
        canvas.yview_moveto(position)

    def add_divider(self, pady=(14, 0)):
        ctk.CTkFrame(self, height=2, fg_color=DIVIDER_COLOR, corner_radius=0).pack(
            fill="x", padx=4, pady=pady
        )

    def add_day_heading(self, text):
        ctk.CTkLabel(
            self, text=text, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x", pady=(10, 2), padx=4)


def _rows_to_appointments(rows):
    """Database rows -> plain dicts the widgets can read."""
    appointments = []
    for row in rows:
        record = dict(row)
        scheduled_time = record["scheduled_time"]
        appointments.append({
            "id": record["id"],
            "scheduled": scheduled_time,
            # A real date object, so consecutive cards can be compared to
            # see when the day changes.
            "date": scheduled_time.date(),
            "time": format_time(scheduled_time),
            # `full_name` is the appointee's name, always present on the
            # row - it is filled in when the appointment is booked, well
            # before a patient record may exist.
            "patient": record["full_name"],
            "reason": record["reason"] or "No reason given",
            "status": record["status"],
            "checked_in_at": record.get("checked_in_at"),
        })
    return appointments


def _signature(appointments):
    """A cheap fingerprint of what is on screen, so a refresh that finds
    nothing changed can skip the redraw (no flicker, no scroll jump)."""
    return tuple(
        (a["id"], a["status"], a["scheduled"], a["patient"], a["reason"], a["checked_in_at"])
        for a in appointments
    )


def _arrival_text(appt):
    """"Checked in 9:02 AM" - with the date too if it wasn't today.
    Falls back to the booked time for a check-in that pre-dates the
    checked_in_at column."""
    arrived = appt["checked_in_at"]
    if arrived is None:
        return "booked for " + appt["time"]
    text = "checked in " + format_time(arrived)
    if arrived.date() != date.today():
        text = "checked in " + arrived.strftime("%b %d") + ", " + format_time(arrived)
    return text


# ===========================================================================
# 1B. NURSE APPOINTMENT BOARD
# The Appointments page body, top to bottom:
#
#    +--------------------------------------------------+
#    |                              <  October 2026  >  |  month filter (right)
#    |  +--------------------------------------------+  |
#    |  | CONSULTING NOW                             |  |  read-only for a nurse
#    |  | Ana Cruz                                   |  |
#    |  +--------------------------------------------+  |
#    |  +--------------------------------------------+  |
#    |  | WAITING QUEUE                              |  |  no buttons: only the
#    |  | #1  Ben Lee   checked in 9:10              |  |  doctor moves them on
#    |  +--------------------------------------------+  |
#    |  TODAY - Monday, October 05                      |  still-scheduled
#    |    card                    [Check in] [Cancel]   |  appointments by day
#    +--------------------------------------------------+
#
# The nurse's only actions live on the scheduled cards:
#   * Check in - the card leaves the list and joins the waiting queue.
#   * Cancel   - the appointment goes straight to History.
# ===========================================================================
class NurseAppointmentBoard(ctk.CTkFrame):
    def __init__(self, parent, controller, doctor_id, on_change=None):
        """
        controller  - an AppointmentController
        doctor_id   - the nurse's assigned doctor
        on_change   - called after a status change succeeds, so the
                      dashboard can refresh other pages (History)
        """
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.doctor_id = doctor_id
        self.on_change = on_change

        today = date.today()
        self.view_year, self.view_month = today.year, today.month
        self._drawn = None  # signature of what is currently on screen

        self._build_month_bar()
        self.list = _ScrollList(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True, pady=(4, 0))

    # -------------------------------------------------------------------
    # Month filter (right side of the window)
    # -------------------------------------------------------------------
    def _build_month_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x")

        # side="right" packs from the right edge inward, so the FIRST
        # widget packed ends up rightmost. Packing next -> label -> prev
        # therefore reads   ◀  October 2026  ▶   from left to right.
        self.next_btn = ctk.CTkButton(
            bar, text="▶", width=36, height=30, fg_color=NAV_BTN_BG,
            command=lambda: self.change_month(1)
        )
        self.next_btn.pack(side="right")

        self.month_label = ctk.CTkLabel(
            bar, text="", width=170, font=ctk.CTkFont(size=15, weight="bold")
        )
        self.month_label.pack(side="right", padx=6)

        self.prev_btn = ctk.CTkButton(
            bar, text="◀", width=36, height=30, fg_color=NAV_BTN_BG,
            command=lambda: self.change_month(-1)
        )
        self.prev_btn.pack(side="right")

    def _is_current_month(self):
        today = date.today()
        return (self.view_year, self.view_month) <= (today.year, today.month)

    def _clamp_view_month(self):
        """Never sit on a past month - not via the buttons, and not after
        the app has been left open past midnight on the 1st."""
        today = date.today()
        if (self.view_year, self.view_month) < (today.year, today.month):
            self.view_year, self.view_month = today.year, today.month

    def change_month(self, delta):
        """Wired to the two arrows. Going back is refused at the current
        month (the button is also greyed out there)."""
        target = add_months(self.view_year, self.view_month, delta)
        today = date.today()
        if target < (today.year, today.month):
            return
        self.view_year, self.view_month = target
        self.refresh(reset_scroll=True)

    def _update_month_bar(self):
        self.month_label.configure(text=month_title(self.view_year, self.view_month))
        self.prev_btn.configure(state="disabled" if self._is_current_month() else "normal")

    # -------------------------------------------------------------------
    # Loading + drawing
    # -------------------------------------------------------------------
    def fetch_consulting(self):
        try:
            rows = self.controller.get_consulting_for_doctor(self.doctor_id)
        except AppointMedError:
            return []
        return _rows_to_appointments(rows)

    def fetch_queue(self):
        try:
            rows = self.controller.get_checkin_queue(self.doctor_id)
        except AppointMedError:
            return []
        queue = _rows_to_appointments(rows)
        if not QUEUE_EARLIEST_FIRST:
            queue.reverse()
        return queue

    def fetch_month(self):
        try:
            rows = self.controller.get_month_for_doctor(
                self.doctor_id, self.view_year, self.view_month
            )
        except AppointMedError:
            return []
        return _rows_to_appointments(rows)

    def refresh(self, reset_scroll=False):
        """Re-read the database and redraw - but only if something is
        different from what is already showing."""
        self._clamp_view_month()
        self._update_month_bar()

        consulting = self.fetch_consulting()
        queue = self.fetch_queue()
        appointments = self.fetch_month()

        signature = (
            self.view_year, self.view_month, date.today(),
            _signature(consulting), _signature(queue), _signature(appointments),
        )
        if signature == self._drawn:
            return
        self._drawn = signature

        scroll_at = 0.0 if reset_scroll else self.list.scroll_position()
        self.list.clear()

        # Order on screen, top to bottom: Consulting -> Queue -> Scheduled.
        self._draw_consulting(consulting)
        if queue:
            self._draw_queue(queue)
        self._draw_month(appointments)

        self.list.restore_scroll(scroll_at)

    # ---- Consulting section (read-only) --------------------------------
    def _draw_consulting(self, consulting):
        """Always drawn, so the nurse can see who is in with the doctor.
        There are no buttons here - finishing a consultation is the
        doctor's job."""
        box = ctk.CTkFrame(
            self.list, corner_radius=10, fg_color=CONSULT_BOX_BG,
            border_width=1, border_color=CONSULT_BOX_BORDER
        )
        box.pack(fill="x", pady=(6, 4))

        header = ctk.CTkFrame(box, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(
            header, text="CONSULTING NOW",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=CONSULT_BOX_TEXT
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="One patient at a time",
            font=ctk.CTkFont(size=11), text_color=MUTED_TEXT
        ).pack(side="right")

        if not consulting:
            ctk.CTkLabel(
                box, text="No patient is being consulted right now.",
                font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
            ).pack(anchor="w", padx=16, pady=(4, 14))
            return

        for index, appt in enumerate(consulting):
            is_last = index == len(consulting) - 1
            row = ctk.CTkFrame(box, corner_radius=8, fg_color="white")
            row.pack(fill="x", padx=10, pady=(4, 12 if is_last else 4))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=(16, 0), pady=10)
            ctk.CTkLabel(
                info, text=appt["patient"],
                font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
            ).pack(fill="x")
            ctk.CTkLabel(
                info, text=appt["reason"] + "   ·   " + _arrival_text(appt),
                font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
            ).pack(fill="x")

    # ---- Waiting queue (no buttons) ------------------------------------
    def _draw_queue(self, queue):
        box = ctk.CTkFrame(
            self.list, corner_radius=10, fg_color=QUEUE_BG,
            border_width=1, border_color=QUEUE_BORDER
        )
        box.pack(fill="x", pady=(6, 4))

        header = ctk.CTkFrame(box, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(
            header, text="WAITING QUEUE  (" + str(len(queue)) + ")",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=QUEUE_TEXT
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=("First in, first served" if QUEUE_EARLIEST_FIRST
                  else "Most recent check-in first"),
            font=ctk.CTkFont(size=11), text_color=MUTED_TEXT
        ).pack(side="right")

        for position, appt in enumerate(queue, start=1):
            is_last = position == len(queue)
            self._draw_queue_row(box, position, appt, bottom_pad=12 if is_last else 4)

    def _draw_queue_row(self, box, position, appt, bottom_pad=4):
        """One waiting patient. Deliberately has NO buttons: once someone
        is checked in, only the doctor can move them to Consulting."""
        row = ctk.CTkFrame(box, corner_radius=8, fg_color="white")
        row.pack(fill="x", padx=10, pady=(4, bottom_pad))

        ctk.CTkLabel(
            row, text="#" + str(position), width=44,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=QUEUE_TEXT
        ).pack(side="left", padx=(10, 4), pady=10)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=10)
        ctk.CTkLabel(
            info, text=appt["patient"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text=appt["reason"] + "   ·   " + _arrival_text(appt),
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT, anchor="w"
        ).pack(fill="x")

    # ---- Scheduled list ------------------------------------------------
    def _draw_month(self, appointments):
        if not appointments:
            ctk.CTkLabel(
                self.list,
                text="No scheduled appointments in "
                     + month_title(self.view_year, self.view_month) + ".",
                text_color=MUTED_TEXT
            ).pack(pady=40)
            return

        # Rows arrive sorted by time, so a new day begins exactly when the
        # date changes. A line goes between one day and the next.
        current_day = None
        for appt in appointments:
            if appt["date"] != current_day:
                if current_day is not None:
                    self.list.add_divider()
                current_day = appt["date"]
                self.list.add_day_heading(day_label(current_day))
            self._draw_card(appt)

    def _draw_card(self, appt):
        """One row: time | patient + reason | [Check in] [Cancel].
        Only Scheduled appointments are ever in this list, so there is no
        status badge - the two buttons are the only things to press."""
        card = ctk.CTkFrame(self.list, corner_radius=10)
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

        # side="right" packs from the edge inward: Cancel first means it
        # sits at the far right, with Check in just to its left.
        ctk.CTkButton(
            card, text="Cancel", width=80, height=28,
            fg_color=CANCEL_BG, hover_color=CANCEL_HOVER,
            command=lambda a=appt: self.change_status(a, "Cancelled")
        ).pack(side="right", padx=(8, 16))

        ctk.CTkButton(
            card, text="Check in", width=90, height=28,
            fg_color=CHECKIN_BG, hover_color=CHECKIN_HOVER,
            command=lambda a=appt: self.change_status(a, "Checked-in")
        ).pack(side="right", padx=(8, 0))

    def change_status(self, appt, new_status):
        """Moves an appointment to `new_status` (Checked-in or Cancelled -
        the only two things a nurse can do). Checked-in joins the waiting
        queue on the redraw; Cancelled lands in History straight away
        (on_change refreshes that page)."""
        try:
            self.controller.update_status(appt["id"], new_status)
        except AppointMedError as e:
            messagebox.showerror("Error", str(e))
            self.refresh()
            return
        self.refresh()
        if self.on_change is not None:
            self.on_change()


# ===========================================================================
# 1C. NURSE HISTORY BOARD
# Every finished (Completed or Cancelled) appointment for the assigned
# doctor, most recent first, grouped by day. Read-only.
# ===========================================================================
class NurseHistoryBoard(ctk.CTkFrame):
    def __init__(self, parent, controller, doctor_id):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.doctor_id = doctor_id
        self._drawn = None

        self.list = _ScrollList(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True)

    def fetch(self):
        try:
            rows = self.controller.get_history_for_doctor(self.doctor_id)
        except AppointMedError:
            return []
        return _rows_to_appointments(rows)

    def refresh(self):
        appointments = self.fetch()
        signature = _signature(appointments)
        if signature == self._drawn:
            return
        self._drawn = signature

        scroll_at = self.list.scroll_position()
        self.list.clear()

        if not appointments:
            ctk.CTkLabel(
                self.list, text="No finished appointments yet.", text_color=MUTED_TEXT
            ).pack(pady=40)
            return

        current_day = None
        for appt in appointments:
            if appt["date"] != current_day:
                if current_day is not None:
                    self.list.add_divider()
                current_day = appt["date"]
                self.list.add_day_heading(current_day.strftime("%A, %B %d, %Y").upper())
            self._draw_card(appt)

        self.list.restore_scroll(scroll_at)

    def _draw_card(self, appt):
        card = ctk.CTkFrame(self.list, corner_radius=10)
        card.pack(fill="x", pady=6)

        ctk.CTkLabel(
            card, text=appt["time"], width=90, font=ctk.CTkFont(size=13, weight="bold")
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

        # Completed or Cancelled - the badge tells them apart.
        status = appt["status"]
        badge_bg, badge_fg = STATUS_COLORS.get(status, STATUS_COLORS["Completed"])
        ctk.CTkLabel(
            card, text=status, fg_color=badge_bg, text_color=badge_fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))


class NurseDashboard(ctk.CTk):
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
    def __init__(self, nurse):
        super().__init__()
        self.nurse = nurse
        self.appointment_controller = AppointmentController()
        self.user_controller = UserController()

        # --- state the sidebar reads and writes ---
        self.sidebar_expanded = True         # is the panel currently open?
        self.current_view = "appointments"   # which page is on screen right now
        self.nav_buttons = {}                # key -> CTkButton, filled in below
        self.pages = {}                      # key -> page frame, filled in below

        # The profile picture lives in the database; fetch it once here
        # so the sidebar can show it the moment the window opens.
        self.avatar_bytes = self.load_avatar()

        self.title(nurse.dashboard_title())
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

        # Round profile picture, or the person's initials if they haven't
        # set one. Kept fresh by refresh_sidebar_profile().
        self.profile_avatar = ctk.CTkLabel(
            self.profile_frame, text="", width=40, height=40,
            fg_color="transparent",
            image=render_avatar(self.avatar_bytes, self.nurse.full_name, 40, bg=AVATAR_BG)
        )
        self.profile_avatar.pack(side="left")

        self.profile_name_label = ctk.CTkLabel(
            self.profile_frame,
            text=getattr(self.nurse, "full_name", "Nurse"),
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
        # top of the others; lift() then picks the visible one.
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.current_view)

    def build_appointments_page(self, parent):
        """The main screen: header row + the nurse's own board for the
        assigned doctor (Consulting Now, waiting queue, then the scheduled
        appointments by day)."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))

        # Kept on self so a rename in "My Account" can update it live.
        self.appointments_title = ctk.CTkLabel(
            header, text=self.nurse.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.appointments_title.pack(side="left")

        ctk.CTkButton(
            header, text="+ Add appointment", width=150,
            command=self.open_add_form
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color=REFRESH_BG,
            command=self.load_appointments
        ).pack(side="right")

        subtitle = ("Managing schedule for Doctor #" + str(self.nurse.assigned_doctor_id) +
                    " — " + date.today().strftime("%A, %B %d"))
        ctk.CTkLabel(
            page, text=subtitle,
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # load_appointments() asks this board to redraw; it must exist
        # before load_appointments() is called in __init__.
        self.board = NurseAppointmentBoard(
            page, self.appointment_controller, self.nurse.assigned_doctor_id,
            # A finished (cancelled) appointment moves to History, so keep
            # that page in step whenever a status changes.
            on_change=self.load_history
        )
        self.board.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def build_profile_page(self, parent):
        """"My Account" - the shared profile screen (photo, name, username,
        password). It lives in views/shared/profile_page.py so every role
        gets the same page; this just hands it this dashboard's user."""
        self.profile_page = ProfilePage(
            parent, self.nurse, "nurse", self.user_controller,
            avatar_bytes=self.avatar_bytes,
            on_change=self.on_profile_changed
        )
        return self.profile_page

    def load_avatar(self):
        """This user's stored picture, or None (also None if the database
        can't be reached - initials are shown instead)."""
        try:
            return self.user_controller.get_avatar(self.nurse.user_id)
        except AppointMedError:
            return None

    def on_profile_changed(self):
        """Called by the profile page after any successful save. It has
        already updated self.nurse in place, so just redraw whatever
        shows the name, title or picture."""
        self.avatar_bytes = self.profile_page.avatar_bytes
        self.refresh_sidebar_profile()
        self.title(self.nurse.dashboard_title())
        self.appointments_title.configure(text=self.nurse.dashboard_title())

    def refresh_sidebar_profile(self):
        """Redraw the avatar and name at the top of the sidebar."""
        self.profile_name_label.configure(text=self.nurse.full_name)
        self.profile_avatar.configure(
            image=render_avatar(self.avatar_bytes, self.nurse.full_name, 40, bg=AVATAR_BG)
        )

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
        """Doctor tab — details of the assigned doctor. Not built yet."""
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
        """History tab — every appointment of the assigned doctor that has
        been Completed or Cancelled. An appointment leaves the
        Appointments page and lands here the moment it is finished."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            page, text="History", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            page, text="Completed and cancelled appointments, most recent first",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        self.history_board = NurseHistoryBoard(
            page, self.appointment_controller, self.nurse.assigned_doctor_id
        )
        self.history_board.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

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
        if key == "history":
            # The doctor completes appointments from another machine, so
            # re-read whenever this page is opened.
            self.load_history()

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
    # 8. APPOINTMENT DATA
    # The drawing and the database calls live in NurseAppointmentBoard /
    # NurseHistoryBoard (sections 1B and 1C above); this section just
    # tells them when to refresh.
    # ===================================================================
    def load_appointments(self):
        """Redraw the appointment board. Called on start-up, after Refresh,
        and after any add/check-in/cancel."""
        self.board.refresh()

    def load_history(self):
        """Redraw the History page."""
        self.history_board.refresh()

    # ------------------------------------------------------------------
    # ADD-APPOINTMENT FORM (a small pop-up window)
    # ------------------------------------------------------------------
    def open_add_form(self):
        """Books either a walk-in or a converted notification (the walk-in
        case is the default here - notifications aren't built yet). The
        appointee's name is collected directly since there isn't a
        patient record yet - one only gets created once a doctor
        actually examines them.

        Date and time are picked from dropdowns instead of typed as free
        text - that removes the whole "did I type the format right?"
        class of mistake, so the only way this form can fail is a real
        business rule (blank name, double-booked slot, etc.)."""
        form = ctk.CTkToplevel(self)
        form.title("Add Appointment")
        form.geometry("380x480")
        form.grab_set()  # modal: blocks clicks on the dashboard behind it

        ctk.CTkLabel(
            form, text="New Appointment", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 16))

        full_name_entry = self.labeled_entry(form, "Patient / appointee name")

        # --- date & time, as dropdowns instead of a typed field ---------
        ctk.CTkLabel(form, text="Date & time", anchor="w").pack(
            fill="x", padx=30, pady=(10, 2)
        )
        date_time_row = ctk.CTkFrame(form, fg_color="transparent")
        date_time_row.pack(padx=30, fill="x")

        date_choices = self._upcoming_date_choices()
        date_combo = ctk.CTkComboBox(
            date_time_row, values=list(date_choices.keys()), width=190
        )
        date_combo.set(next(iter(date_choices)))
        date_combo.pack(side="left")

        hour_combo = ctk.CTkComboBox(
            date_time_row, values=[f"{h:02d}" for h in range(24)], width=52
        )
        hour_combo.set("09")
        hour_combo.pack(side="left", padx=(6, 2))

        ctk.CTkLabel(date_time_row, text=":").pack(side="left")

        minute_combo = ctk.CTkComboBox(
            date_time_row, values=["00", "15", "30", "45"], width=52
        )
        minute_combo.set("00")
        minute_combo.pack(side="left", padx=(2, 0))

        reason_entry = self.labeled_entry(form, "Reason for visit")

        status_label = ctk.CTkLabel(form, text="", text_color=ERROR_TEXT, wraplength=300)
        status_label.pack(pady=(4, 0))

        # Defined inside open_add_form() so it can read the widgets above
        # directly, without storing them all on self.
        def submit():
            try:
                full_name = full_name_entry.get().strip()
                reason = reason_entry.get().strip()

                # The combo boxes can only ever hold values we put there,
                # so this can't raise ValueError the way typed text could.
                chosen_date = date_choices[date_combo.get()]
                chosen_time = datetime.strptime(
                    f"{hour_combo.get()}:{minute_combo.get()}", "%H:%M"
                ).time()
                scheduled_time = datetime.combine(chosen_date, chosen_time)

                # No patient record yet at booking time - that only gets
                # created once a doctor examines the appointee, so this
                # is always None here.
                self.appointment_controller.add_appointment(
                    full_name=full_name,
                    doctor_id=self.nurse.assigned_doctor_id,
                    nurse_id=self.nurse.user_id,
                    scheduled_time=scheduled_time,
                    reason=reason,
                    patient_id=None,
                )
                form.destroy()
                self.load_appointments()
                messagebox.showinfo(
                    "Appointment booked",
                    full_name + " is scheduled for " +
                    format_datetime(scheduled_time) + "."
                )
            except AppointMedError as e:
                # Business-rule problems (slot taken, blank name, etc.) -
                # the only kind of error this form can still hit.
                status_label.configure(text=str(e))

        ctk.CTkButton(form, text="Add appointment", command=submit).pack(pady=24)

    @staticmethod
    def _upcoming_date_choices(days_ahead=30):
        """Today plus the next `days_ahead` days, as a dict mapping a
        friendly label (what shows up in the dropdown) to the actual
        date object it stands for. A dict keeps the two in lockstep
        without needing a second, parallel list to search through."""
        choices = {}
        for offset in range(days_ahead + 1):
            day = date.today() + timedelta(days=offset)
            label = day.strftime("%a, %b %d %Y")
            if offset == 0:
                label += " (today)"
            choices[label] = day
        return choices

    @staticmethod
    def labeled_entry(parent, label_text):
        """Label above an entry box — the pattern every form field uses."""
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(
            fill="x", padx=30, pady=(10, 2)
        )
        entry = ctk.CTkEntry(parent, width=300)
        entry.pack(padx=30)
        return entry