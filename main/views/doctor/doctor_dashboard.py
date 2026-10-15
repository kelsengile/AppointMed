from views.shared.history import HistoryView
from views.shared.settings_view import SettingsView
"""
Doctor's dashboard — built with CustomTkinter.

Same two-part layout as the other dashboards:

    +-----------+--------------------------------+
    |  sidebar  |         content area           |
    | (nav)     |  one "page" per nav button     |
    +-----------+--------------------------------+

Pages with real content right now:
  * "Appointments" - the doctor's main page (section 1B-1D):
        LEFT   a big month CALENDAR. Days that have appointments are
               highlighted; clicking a day opens that day's appointments
               in the panel on the right.
        RIGHT  a panel with two views, switched at the top:
                 - "Pending"       Consulting Now, the waiting queue and
                                   the still-scheduled appointments
                 - "Selected date" the appointments of the clicked day
    The doctor can NOT add appointments any more - the assigned nurse
    books them. They appear here by themselves (auto-refresh) or when
    the Refresh button is pressed.
  * "Doctor"  - profile, live "today at a glance" numbers, details.
  * "Room"    - live room status from the database (section 5).
  * "History" - every appointment that has been Completed or Cancelled.
  * "Help"    - FAQ.

HOW THE PAGES STAY CONNECTED
    Every change (check in, consult, complete, cancel, booking, room
    maintenance) ends up in refresh_linked_pages() / refresh_all() in
    section 8, which redraws the calendar, History, the Doctor page's
    numbers and the Room page together. The same thing runs every
    AUTO_REFRESH_MS, so a nurse's bookings show up on their own.

HOW THIS FILE IS ORGANISED (read the section banners as you scroll):
    1. SETTINGS           — colours, sizes, nav items. Tweak things here first.
    1A. BOARD HELPERS     — small functions/classes the boards use
    1B. APPOINTMENT BOARD — the "Pending" view (consulting / queue / scheduled)
    1C. HISTORY BOARD     — the doctor's History page body
    1D. CALENDAR + PANEL  — the month calendar and the right-hand panel
    2. WINDOW SETUP       — __init__ / build_ui
    3. SIDEBAR            — building the nav panel
    4. SIDEBAR ANIMATION  — the collapse/expand slide
    5. CONTENT PAGES      — one build_*_page() per screen
    6. PLACEHOLDER PAGE   — the "not built yet" screen
    7. PAGE ROUTING       — which page is visible
    8. APPOINTMENT DATA   — telling the boards when to refresh

WANT TO ADD A BRAND-NEW SCREEN? Three small steps:
    a) add a dict to NAV_ITEMS
    b) write a build_yourthing_page() in section 5
    c) register it in the page_builders dict inside build_content_area()
Anything you skip step (b) and (c) for automatically gets a placeholder.
"""

import calendar
import time
from datetime import date, datetime, timedelta

import customtkinter as ctk
from tkinter import messagebox

from controllers.appointment_controller import AppointmentController
from controllers.room_controller import RoomController, attach_rooms
from controllers.user_controller import UserController
from views.shared.invoice_page import InvoicePage
from utils.exceptions import AppointMedError
from utils.avatar import render_avatar
from utils.formatting import format_time

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

DOCTOR_BADGE_BG = "#E3F0FF"
DOCTOR_BADGE_FG = "#2B6CB0"

# --- appointment board colours (doctor's board) ---------------------------
DIVIDER_COLOR = "gray75"

CHECKIN_BG = "#2B6CB0"
CHECKIN_HOVER = "#2C5282"
CONSULT_BG = "#2C7A7B"
CONSULT_HOVER = "#285E61"
COMPLETE_BG = "#2F855A"
COMPLETE_HOVER = "#276749"
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
# For Rooms Page
# (the rooms themselves now come from the database - see
#  controllers/room_controller.py)
# ===========================================================================

# Room status badge colours: (background, text) — same idea as STATUS_COLORS.
ROOM_STATUS_COLORS = {
    "Available":   ("#E3F6E8", "#2F855A"),
    "Occupied":    ("#FFF1D6", "#B7791F"),
    "Maintenance": ("#FBE7E7", "#C53030"),
}

# ===========================================================================
# For the Calendar + right-hand panel (Appointments page)
# ===========================================================================
SIDE_PANEL_WIDTH = 460        # the right-hand panel (Pending / Selected date)
CAL_HAS_BG = "#BEE3F8"        # a day that has appointments
CAL_HAS_FG = "#2C5282"
CAL_SELECTED_BG = "#2B6CB0"   # the day you clicked
CAL_HOVER = "#E2E8F0"
CAL_TODAY_BORDER = "#2B6CB0"

# ===========================================================================
# For FAQ (Help Page)
# ===========================================================================

FAQ_HOVER = "gray85"

# (section title, [(question, answer), ...]) — edit the text freely.
FAQ_SECTIONS = [
    ("APPOINTMENTS", [
        ("How does the waiting queue work?",
         "When a scheduled patient is checked in, they move to the Waiting "
         "Queue. Patients are served first-in, first-served, so the one who "
         "checked in earliest is #1."),
        ("Why is the 'Consulting' button greyed out?",
         "Only one patient can be consulted at a time. Press 'Complete' on "
         "the current patient and the button becomes available again."),
        ("What happens when I press Complete or Cancel?",
         "The appointment leaves the Appointments page and is saved in "
         "History, marked as Completed or Cancelled."),
        ("How do I see my appointments on a certain date?",
         "On the Appointments page, days that have appointments are "
         "highlighted on the calendar. Click a day and its appointments "
         "open in the panel on the right. Switch back with 'Pending'."),
        ("Who books my appointments?",
         "Your assigned nurse/secretary books them. Doctors can't add "
         "appointments themselves - ask your nurse to add a follow-up."),
        ("A nurse booked a patient but I can't see it yet.",
         "The page refreshes by itself every 20 seconds. You can also press "
         "the Refresh button at the top of the Appointments page."),
    ]),
    ("ACCOUNT", [
        ("How do I change my photo, name or password?",
         "Click your name at the top of the sidebar to open My Account."),
        ("I can't log in anymore.",
         "Please contact the clinic administrator to have your password reset."),
    ]),
]

SUPPORT_CONTACT = "Clinic Administrator  ·  admin@yourclinic.example  ·  Local 100"

# ===========================================================================
# 1A. BOARD HELPERS
# Small pieces the doctor's boards below are built from.
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
    top. Rebuilding a long month every few seconds would otherwise throw
    the reader away from wherever they had scrolled to."""

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
# Class of FAQ
# ===========================================================================
class _FAQItem(ctk.CTkFrame):
    """One collapsible question. Click the question to show/hide the answer."""

    def __init__(self, parent, question, answer):
        super().__init__(parent, corner_radius=10)
        self.question = question
        self._open = False

        self.header = ctk.CTkButton(
            self, text="▸   " + question, anchor="w", height=40,
            fg_color="transparent", hover_color=FAQ_HOVER,
            text_color=("gray10", "gray90"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.toggle
        )
        self.header.pack(fill="x", padx=6, pady=2)

        self.answer = ctk.CTkLabel(
            self, text=answer, wraplength=620, justify="left", anchor="w",
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
        )

    def toggle(self):
        self._open = not self._open
        arrow = "▾" if self._open else "▸"
        self.header.configure(text=arrow + "   " + self.question)
        if self._open:
            self.answer.pack(fill="x", padx=24, pady=(0, 12))
        else:
            self.answer.pack_forget()

# ===========================================================================
# 1B. DOCTOR APPOINTMENT BOARD  (the "Pending" view of the right-hand panel)
#
#    +------------------------------------+
#    |              <  October 2026  >    |  month filter (right)
#    |  +------------------------------+  |
#    |  | CONSULTING NOW               |  |  one patient at a time
#    |  | Ana Cruz         [Complete]  |  |
#    |  +------------------------------+  |
#    |  +------------------------------+  |
#    |  | WAITING QUEUE                |  |  checked-in patients,
#    |  | #1  Ben Lee   [Consulting]   |  |  first in, first served
#    |  +------------------------------+  |
#    |  TODAY - Monday, October 05        |  still-scheduled
#    |    card         [Check in][Cancel] |  appointments by day
#    +------------------------------------+
#
# Doctor-only powers on this board:
#   * Consulting - moves the first waiting patient in (only if nobody is
#     being consulted; the button is greyed out otherwise).
#   * Complete   - finishes the current consultation, straight to History.
# ===========================================================================
class DoctorAppointmentBoard(ctk.CTkFrame):
    def __init__(self, parent, controller, doctor_id, on_change=None):
        """
        controller  - an AppointmentController
        doctor_id   - the logged-in doctor's own id
        on_change   - called after a status change succeeds, so the
                      dashboard can refresh the other pages
        """
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.room_controller = RoomController()
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
        # Put each appointment's room name after its reason text.
        attach_rooms(self.room_controller, consulting, queue, appointments)

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
            self._draw_queue(queue, consulting_busy=bool(consulting))
        self._draw_month(appointments)

        self.list.restore_scroll(scroll_at)

    # ---- Consulting section --------------------------------------------
    def _draw_consulting(self, consulting):
        """Always drawn, so it is obvious at a glance whether the
        consulting slot is free. Each row has a Complete button."""
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
 
            # Button FIRST so it is never squeezed out.
            ctk.CTkButton(
                row, text="Complete", width=100, height=28,
                fg_color=COMPLETE_BG, hover_color=COMPLETE_HOVER,
                command=lambda a=appt: self.change_status(a, "Completed")
            ).pack(side="right", padx=(8, 12))
 
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=(16, 0), pady=10)
            ctk.CTkLabel(
                info, text=appt["patient"],
                font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
            ).pack(fill="x")
            ctk.CTkLabel(
                info, text=appt["reason"] + "   ·   " + _arrival_text(appt),
                font=ctk.CTkFont(size=12), text_color=MUTED_TEXT,
                anchor="w", justify="left", wraplength=240
            ).pack(fill="x")

    # ---- Waiting queue -------------------------------------------------
    def _draw_queue(self, queue, consulting_busy):
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
            self._draw_queue_row(
                box, position, appt, consulting_busy,
                bottom_pad=12 if is_last else 4
            )

    def _draw_queue_row(self, box, position, appt, consulting_busy, bottom_pad=4):
        row = ctk.CTkFrame(box, corner_radius=8, fg_color="white")
        row.pack(fill="x", padx=10, pady=(4, bottom_pad))
 
        # Button FIRST, so it always keeps its full width (see top of file).
        # Only one consultation at a time, so it is greyed out while somebody
        # is still in. (The controller enforces this too.)
        ctk.CTkButton(
            row, text="Consulting", width=100, height=28,
            fg_color=CONSULT_BG, hover_color=CONSULT_HOVER,
            state="disabled" if consulting_busy else "normal",
            command=lambda a=appt: self.change_status(a, "Consulting")
        ).pack(side="right", padx=(8, 12))
 
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
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT,
            anchor="w", justify="left", wraplength=210
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
        """One row: time | patient + reason | [Check in] [Cancel]."""
        card = ctk.CTkFrame(self.list, corner_radius=10)
        card.pack(fill="x", pady=6)
 
        # Buttons FIRST. side="right" packs from the edge inward: Cancel
        # first means it sits at the far right, Check in just to its left.
        ctk.CTkButton(
            card, text="Cancel", width=70, height=28,
            fg_color=CANCEL_BG, hover_color=CANCEL_HOVER,
            command=lambda a=appt: self.change_status(a, "Cancelled")
        ).pack(side="right", padx=(6, 12))
 
        ctk.CTkButton(
            card, text="Check in", width=80, height=28,
            fg_color=CHECKIN_BG, hover_color=CHECKIN_HOVER,
            command=lambda a=appt: self.change_status(a, "Checked-in")
        ).pack(side="right", padx=(6, 0))
 
        ctk.CTkLabel(
            card, text=appt["time"], width=72,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(12, 6), pady=14)
 
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=14)
        ctk.CTkLabel(
            info, text=appt["patient"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text=appt["reason"], font=ctk.CTkFont(size=12),
            text_color=MUTED_TEXT, anchor="w", justify="left", wraplength=140
        ).pack(fill="x")

    def change_status(self, appt, new_status):
        """Moves an appointment to `new_status` (Checked-in, Consulting,
        Completed, Cancelled). Each one leaves its current section on the
        redraw and appears in the next one; Completed and Cancelled land
        in History straight away (on_change refreshes the other pages)."""
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
# 1C. DOCTOR HISTORY BOARD
# Every finished (Completed or Cancelled) appointment for this doctor,
# most recent first, grouped by day. Read-only.
# ===========================================================================
class DoctorHistoryBoard(ctk.CTkFrame):
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


# ===========================================================================
# 1D. DOCTOR CALENDAR  +  RIGHT-HAND PANEL
#
#   +-------------------------------+  +-----------------------------+
#   |  ◀      October 2026      ▶   |  | [ Pending | Selected date ] |
#   |  Su  Mo  Tu  We  Th  Fr  Sa   |  |                             |
#   |   .   .   1   2   3   4   5   |  |  Pending       = the board  |
#   |   ...                         |  |  Selected date = the clicked|
#   |  (the big main calendar)      |  |                  day's list |
#   +-------------------------------+  +-----------------------------+
#      highlighted day = has appointments
#      blue day        = the one you clicked
#      outlined day    = today
#
# The 42 day buttons are created ONCE and only re-coloured on refresh, so
# the calendar never flickers. It marks every appointment this doctor has
# (scheduled ones, plus anyone already checked in or being consulted), which
# the assigned nurse books from their own dashboard.
#
# The calendar does not know about the panel. It just calls two optional
# callbacks the dashboard fills in:
#   on_select  - the doctor CLICKED a day  -> panel shows the day's list
#   on_refresh - data was (re)loaded       -> panel redraws that list
# ===========================================================================
class DoctorCalendar(ctk.CTkFrame):
    WEEKDAYS = ("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa")

    def __init__(self, parent, controller, room_controller, doctor_id):
        super().__init__(parent, corner_radius=10)
        self.controller = controller
        self.room_controller = room_controller
        self.doctor_id = doctor_id

        today = date.today()
        self.view_year, self.view_month = today.year, today.month
        self.selected = today
        self.by_day = {}      # date -> [appointment dicts], filled by refresh()
        self._drawn = None

        self.on_select = None   # called with the clicked date
        self.on_refresh = None  # called after every refresh()

        self._build_month_bar()
        self._build_grid()

    # ---- building (once) -------------------------------------------------
    def _build_month_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(14, 6))

        self.prev_btn = ctk.CTkButton(
            bar, text="◀", width=36, height=30, fg_color=NAV_BTN_BG,
            command=lambda: self.change_month(-1)
        )
        self.prev_btn.pack(side="left")
        self.next_btn = ctk.CTkButton(
            bar, text="▶", width=36, height=30, fg_color=NAV_BTN_BG,
            command=lambda: self.change_month(1)
        )
        self.next_btn.pack(side="right")
        self.month_label = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.month_label.pack(side="left", expand=True)

    def _build_grid(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=12, pady=(2, 2))

        # Equal-weight columns/rows make the day buttons stretch to fill
        # whatever space the calendar has.
        for column in range(7):
            grid.columnconfigure(column, weight=1, uniform="day")
        for row in range(1, 7):
            grid.rowconfigure(row, weight=1, uniform="week")

        for column, name in enumerate(self.WEEKDAYS):
            ctk.CTkLabel(
                grid, text=name, height=24,
                font=ctk.CTkFont(size=12, weight="bold"), text_color=MUTED_TEXT
            ).grid(row=0, column=column, padx=2, sticky="ew")

        self.cells = []
        for index in range(42):  # 6 weeks x 7 days always covers a month
            button = ctk.CTkButton(
                grid, text="", width=40, height=40, corner_radius=8,
                fg_color="transparent", hover_color=CAL_HOVER,
                text_color=("gray10", "gray90"), font=ctk.CTkFont(size=14)
            )
            button.grid(row=1 + index // 7, column=index % 7, padx=2, pady=2,
                        sticky="nsew")
            self.cells.append(button)

        ctk.CTkLabel(
            self, text="Highlighted days have appointments — click a day to see them",
            font=ctk.CTkFont(size=11), text_color=MUTED_TEXT
        ).pack(pady=(2, 10))

    # ---- month navigation --------------------------------------------------
    def _clamp_view_month(self):
        today = date.today()
        if (self.view_year, self.view_month) < (today.year, today.month):
            self.view_year, self.view_month = today.year, today.month

    def change_month(self, delta):
        target = add_months(self.view_year, self.view_month, delta)
        today = date.today()
        if target < (today.year, today.month):
            return
        self.view_year, self.view_month = target
        # Land on today in the current month, otherwise on the 1st.
        if target == (today.year, today.month):
            self.selected = today
        else:
            self.selected = date(target[0], target[1], 1)
        self.refresh()

    def select(self, day):
        """A day button was clicked: mark it and tell the panel."""
        self.selected = day
        self._paint()
        if self.on_select is not None:
            self.on_select(day)

    # ---- loading -------------------------------------------------------------
    def _fetch_all(self):
        try:
            month_rows = self.controller.get_month_for_doctor(
                self.doctor_id, self.view_year, self.view_month
            )
            active_rows = (list(self.controller.get_consulting_for_doctor(self.doctor_id))
                           + list(self.controller.get_checkin_queue(self.doctor_id)))
        except AppointMedError:
            return []

        appointments = _rows_to_appointments(month_rows)
        seen = {a["id"] for a in appointments}
        # Checked-in / consulting patients have left the "scheduled" list,
        # but their day should stay marked, so add them back for this month.
        for appt in _rows_to_appointments(active_rows):
            in_month = (appt["date"].year, appt["date"].month) == (self.view_year, self.view_month)
            if appt["id"] not in seen and in_month:
                appointments.append(appt)
        appointments.sort(key=lambda a: a["scheduled"])
        attach_rooms(self.room_controller, appointments)
        return appointments

    def refresh(self):
        """Re-read and repaint - only if something actually changed. The
        panel is always told afterwards, so its "Selected date" list stays
        in step (it skips its own redraw if nothing changed)."""
        self._clamp_view_month()
        appointments = self._fetch_all()
        signature = (self.view_year, self.view_month, self.selected,
                     date.today(), _signature(appointments))
        if signature != self._drawn:
            self._drawn = signature

            self.by_day = {}
            for appt in appointments:
                self.by_day.setdefault(appt["date"], []).append(appt)
            self._paint()

        if self.on_refresh is not None:
            self.on_refresh()

    # ---- drawing -------------------------------------------------------------
    def _paint(self):
        today = date.today()
        self.month_label.configure(text=month_title(self.view_year, self.view_month))
        self.prev_btn.configure(
            state="disabled" if (self.view_year, self.view_month) <= (today.year, today.month)
            else "normal"
        )

        cells = [d for week in calendar.Calendar(firstweekday=6)
                 .monthdatescalendar(self.view_year, self.view_month) for d in week]
        while len(cells) < 42:
            cells.append(cells[-1] + timedelta(days=1))

        for button, day in zip(self.cells, cells):
            if day.month != self.view_month:
                # A day from the neighbouring month - leave the cell blank.
                button.configure(text="", state="disabled", fg_color="transparent",
                                 border_width=0)
                continue

            has_appointments = bool(self.by_day.get(day))
            if day == self.selected:
                fg, text_color = CAL_SELECTED_BG, "white"
            elif has_appointments:
                fg, text_color = CAL_HAS_BG, CAL_HAS_FG
            else:
                fg, text_color = "transparent", ("gray10", "gray90")

            button.configure(
                text=str(day.day), state="normal", fg_color=fg, text_color=text_color,
                border_width=2 if day == today else 0, border_color=CAL_TODAY_BORDER,
                font=ctk.CTkFont(size=14, weight="bold" if has_appointments else "normal"),
                command=lambda d=day: self.select(d)
            )


class DoctorSidePanel(ctk.CTkFrame):
    """The right-hand panel. A two-button switch at the top picks the view:

        Pending        - the doctor's board (Consulting Now, waiting queue,
                         scheduled appointments). This is the default.
        Selected date  - the appointments of the day clicked on the
                         calendar. Clicking a day jumps to this view by
                         itself, so the details "pop up" on the right.
    """
    PENDING = "Pending"
    DATE = "Selected date"

    def __init__(self, parent, calendar_panel, controller, doctor_id, on_change=None):
        super().__init__(parent, width=SIDE_PANEL_WIDTH, corner_radius=10)
        # Keep the panel exactly SIDE_PANEL_WIDTH wide whatever is inside.
        self.pack_propagate(False)
        self.calendar_panel = calendar_panel
        self._drawn = None

        self.switcher = ctk.CTkSegmentedButton(
            self, values=[self.PENDING, self.DATE], command=self._show_view
        )
        self.switcher.pack(fill="x", padx=12, pady=(12, 6))
        self.switcher.set(self.PENDING)

        # --- view 1: the pending board -----------------------------------
        self.pending_view = ctk.CTkFrame(self, fg_color="transparent")
        self.board = DoctorAppointmentBoard(
            self.pending_view, controller, doctor_id, on_change=on_change
        )
        self.board.pack(fill="both", expand=True)

        # --- view 2: the clicked day's appointments ----------------------
        self.date_view = ctk.CTkFrame(self, fg_color="transparent")
        self.date_heading = ctk.CTkLabel(
            self.date_view, text="", anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=MUTED_TEXT
        )
        self.date_heading.pack(fill="x", padx=8, pady=(4, 2))
        self.date_list = _ScrollList(self.date_view, fg_color="transparent")
        self.date_list.pack(fill="both", expand=True)

        self._show_view(self.PENDING)

    # ---- switching -------------------------------------------------------
    def _show_view(self, value):
        self.pending_view.pack_forget()
        self.date_view.pack_forget()
        if value == self.DATE:
            self.date_view.pack(fill="both", expand=True, padx=6, pady=(0, 8))
        else:
            self.pending_view.pack(fill="both", expand=True, padx=6, pady=(0, 8))

    def show_date(self, day=None):
        """Called by the calendar when a day is clicked."""
        self.switcher.set(self.DATE)
        self._show_view(self.DATE)
        self.refresh_day()

    # ---- drawing the selected day -------------------------------------------
    def refresh_day(self):
        """Redraw the clicked day's list from the calendar's data. Does
        nothing if that day's data has not changed."""
        day = self.calendar_panel.selected
        items = self.calendar_panel.by_day.get(day, [])
        signature = (day, _signature(items))
        if signature == self._drawn:
            return
        self._drawn = signature

        self.date_heading.configure(text=day_label(day))
        scroll_at = self.date_list.scroll_position()
        self.date_list.clear()

        if not items:
            ctk.CTkLabel(
                self.date_list, text="No appointments on this day.",
                font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
            ).pack(pady=30)
            return

        for appt in items:
            row = ctk.CTkFrame(self.date_list, corner_radius=8)
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(
                row, text=appt["time"], width=72, font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="left", padx=(10, 4), pady=10)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=8)
            ctk.CTkLabel(
                info, text=appt["patient"], anchor="w",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(fill="x")
            detail = appt["reason"]
            if appt["status"] != "Scheduled":
                detail += "   ·   " + appt["status"]
            ctk.CTkLabel(
                info, text=detail, anchor="w", justify="left", wraplength=290,
                font=ctk.CTkFont(size=11), text_color=MUTED_TEXT
            ).pack(fill="x")

        self.date_list.restore_scroll(scroll_at)


class DoctorDashboard(ctk.CTk):
    # --- sizes you may want to tweak -------------------------------------
    WINDOW_SIZE = "1280x720"
    SIDEBAR_EXPANDED_WIDTH = 210
    SIDEBAR_COLLAPSED_WIDTH = 64
    # The animation runs for a fixed DURATION and recomputes the exact
    # width needed at each point in time (eased with ease-in-out-cubic),
    # instead of moving a constant number of pixels per tick — that's what
    # keeps it smooth instead of jerky. FRAME_MS is just how often we
    # redraw: smaller = smoother.
    ANIMATION_DURATION_S = 0.32
    ANIMATION_FRAME_MS = 8

    # How often the schedule re-reads the database on its own. A nurse
    # books appointments from a different machine, so without this the
    # doctor would only ever see what existed the moment they logged in
    # (or last pressed Refresh).
    AUTO_REFRESH_MS = 5000

    # ===================================================================
    # 2. WINDOW SETUP
    # ===================================================================
    def __init__(self, doctor):
        super().__init__()
        self.doctor = doctor
        self.appointment_controller = AppointmentController()
        self.room_controller = RoomController()
        self.user_controller = UserController()

        # --- state the sidebar reads and writes ---
        self.sidebar_expanded = True         # is the panel currently open?
        self.current_view = "appointments"   # which page is on screen right now
        self.nav_buttons = {}                # key -> CTkButton, filled in below
        self.pages = {}                      # key -> page frame, filled in below

        # The profile picture lives in the database; fetch it once here
        # so the sidebar can show it the moment the window opens.
        self.avatar_bytes = self.load_avatar()

        self.title(doctor.dashboard_title())
        self.geometry(self.WINDOW_SIZE)
        self.build_ui()
        self.refresh_all()
        self.schedule_auto_refresh()

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
            image=render_avatar(self.avatar_bytes, self.doctor.full_name, 40, bg=AVATAR_BG)
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
        # top of the others; lift() then picks the visible one.
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.current_view)

    def build_appointments_page(self, parent):
        """The main screen: header row, then the big calendar on the left
        and the right-hand panel (Pending / Selected date) beside it.
        There is no "Add appointment" button: the assigned nurse books."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        # Kept on self so a rename in "My Account" can update it live.
        self.appointments_title = ctk.CTkLabel(
            header, text=self.doctor.dashboard_title(),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.appointments_title.pack(side="left")

        ctk.CTkButton(
            header, text="Refresh", width=90, fg_color=REFRESH_BG,
            command=self.refresh_all
        ).pack(side="right")
        # Shows when the page last re-read the database, so a press of
        # Refresh (or the 20-second timer) is visibly doing something.
        self.last_updated_label = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=11), text_color=MUTED_TEXT
        )
        self.last_updated_label.pack(side="right", padx=(0, 10))

        ctk.CTkLabel(
            page,
            text="Click a highlighted date to see its appointments — newly booked visits appear automatically",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        content = ctk.CTkFrame(page, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.calendar_panel = DoctorCalendar(
            content, self.appointment_controller, self.room_controller,
            self.doctor.user_id
        )
        self.side_panel = DoctorSidePanel(
            content, self.calendar_panel, self.appointment_controller,
            self.doctor.user_id,
            # Any status change must update the calendar, History, the
            # Doctor page's numbers and the Room page too.
            on_change=self.on_board_change
        )
        # The fixed-width panel is packed FIRST so it keeps its width and
        # the calendar takes whatever space is left.
        self.side_panel.pack(side="right", fill="y", padx=(12, 0))
        self.calendar_panel.pack(side="left", fill="both", expand=True)

        # load_appointments() asks this board to redraw; it must exist
        # before refresh_all() is called in __init__.
        self.board = self.side_panel.board

        # Wire the calendar to the panel: a click opens that day's list,
        # and every data refresh keeps the list up to date.
        self.calendar_panel.on_select = self.side_panel.show_date
        self.calendar_panel.on_refresh = self.side_panel.refresh_day

        return page

    def build_profile_page(self, parent):
        """"My Account" - the shared profile screen (photo, name, username,
        password). It lives in views/shared/profile_page.py so every role
        gets the same page; this just hands it this dashboard's user."""
        self.profile_page = ProfilePage(
            parent, self.doctor, "doctor", self.user_controller,
            avatar_bytes=self.avatar_bytes,
            on_change=self.on_profile_changed
        )
        return self.profile_page

    def load_avatar(self):
        """This user's stored picture, or None (also None if the database
        can't be reached - initials are shown instead)."""
        try:
            return self.user_controller.get_avatar(self.doctor.user_id)
        except AppointMedError:
            return None

    def on_profile_changed(self):
        """Called by the profile page after any successful save. It has
        already updated self.doctor in place, so just redraw whatever
        shows the name, title or picture."""
        self.avatar_bytes = self.profile_page.avatar_bytes
        self.refresh_sidebar_profile()
        self.title(self.doctor.dashboard_title())
        self.appointments_title.configure(text=self.doctor.dashboard_title())
        self.refresh_doctor_page()

    def refresh_sidebar_profile(self):
        """Redraw the avatar and name at the top of the sidebar."""
        self.profile_name_label.configure(text=self.doctor.full_name)
        self.profile_avatar.configure(
            image=render_avatar(self.avatar_bytes, self.doctor.full_name, 40, bg=AVATAR_BG)
        )

    # ---------------------------------------------------------------
    # DOCTOR PAGE — profile card, today's numbers, professional details
    # ---------------------------------------------------------------
    def build_doctor_page(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            page, text="Doctor", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            page, text="Your profile and a snapshot of today's clinic activity",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        body = _ScrollList(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # --- profile card ---
        card = ctk.CTkFrame(body, corner_radius=10)
        card.pack(fill="x", pady=6)

        self.doctor_avatar = ctk.CTkLabel(
            card, text="", width=72, height=72, fg_color="transparent",
            image=render_avatar(self.avatar_bytes, self.doctor.full_name, 72, bg=AVATAR_BG)
        )
        self.doctor_avatar.pack(side="left", padx=20, pady=20)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=20)
        self.doctor_name_label = ctk.CTkLabel(
            info, text=self.doctor.full_name, anchor="w",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.doctor_name_label.pack(fill="x")
        self.doctor_spec_badge = ctk.CTkLabel(
            info, text=getattr(self.doctor, "specialization", "General Practice"),
            fg_color=DOCTOR_BADGE_BG, text_color=DOCTOR_BADGE_FG,
            corner_radius=8, height=24, width=160,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.doctor_spec_badge.pack(anchor="w", pady=(4, 2))
        self.doctor_username_label = ctk.CTkLabel(
            info, text="@" + getattr(self.doctor, "username", ""),
            anchor="w", font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
        )
        self.doctor_username_label.pack(fill="x")

        ctk.CTkButton(
            card, text="Edit profile", width=110,
            command=lambda: self.switch_view(PROFILE_KEY)
        ).pack(side="right", padx=20)

        # --- today at a glance ---
        body.add_day_heading("TODAY AT A GLANCE")
        stats_row = ctk.CTkFrame(body, fg_color="transparent")
        stats_row.pack(fill="x")
        self.doctor_stat_labels = {}
        for key, caption in (
            ("consulting", "Consulting now"),
            ("waiting",    "In waiting queue"),
            ("scheduled",  "Scheduled today"),
            ("completed",  "Completed today"),
        ):
            tile = ctk.CTkFrame(stats_row, corner_radius=10)
            tile.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
            number = ctk.CTkLabel(tile, text="–", font=ctk.CTkFont(size=26, weight="bold"))
            number.pack(pady=(14, 0))
            ctk.CTkLabel(
                tile, text=caption, font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
            ).pack(pady=(0, 14))
            self.doctor_stat_labels[key] = number

        # --- professional details ---
        body.add_day_heading("PROFESSIONAL DETAILS")
        details = ctk.CTkFrame(body, corner_radius=10)
        details.pack(fill="x", pady=4)
        self._detail_row(details, "Specialization",
                         getattr(self.doctor, "specialization", "General Practice"))
        # The room of the patient being consulted right now (from the
        # database) - updated by load_doctor_stats().
        self.doctor_room_value = self._detail_row(details, "Current room", "—")
        self._detail_row(details, "Consultation hours", "Mon – Fri,  9:00 AM – 5:00 PM")
        self._detail_row(details, "Doctor ID", str(self.doctor.user_id), last=True)

        return page

    @staticmethod
    def _detail_row(parent, label, value, last=False):
        """One "label   value" line. Returns the value label so a caller
        can update it later."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(10, 14 if last else 0))
        ctk.CTkLabel(
            row, text=label, width=160, anchor="w",
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
        ).pack(side="left")
        value_label = ctk.CTkLabel(
            row, text=value, anchor="w", font=ctk.CTkFont(size=13, weight="bold")
        )
        value_label.pack(side="left")
        return value_label

    def load_doctor_stats(self):
        """Fill the four tiles (and the 'Current room' line).
 
        What was wrong before:
          * ONE failed query made the method return early, leaving EVERY
            tile on "–". Now each tile loads on its own, and a failure is
            printed to the console instead of hiding silently.
          * "Completed today" compared the appointment's BOOKED date with
            today, so a visit booked for another day was never counted
            even though it was finished today. It now uses the day the
            patient actually checked in (falling back to the booked day).
        """
        uid = self.doctor.user_id
        today = date.today()
        control = self.appointment_controller
        labels = self.doctor_stat_labels
 
        def fetch(call, *args):
            try:
                return call(*args)
            except AppointMedError as e:
                print("[Doctor page] could not load: " + str(e))
                return None
 
        consulting_rows = fetch(control.get_consulting_for_doctor, uid)
        queue_rows = fetch(control.get_checkin_queue, uid)
        month_rows = fetch(control.get_month_for_doctor, uid, today.year, today.month)
        history_rows = fetch(control.get_history_for_doctor, uid)
 
        consulting = []
        if consulting_rows is not None:
            consulting = _rows_to_appointments(consulting_rows)
            labels["consulting"].configure(text=str(len(consulting)))
 
        if queue_rows is not None:
            labels["waiting"].configure(text=str(len(list(queue_rows))))
 
        if month_rows is not None:
            # Still Scheduled (not yet checked in) AND booked for today.
            scheduled_today = sum(
                1 for a in _rows_to_appointments(month_rows) if a["date"] == today
            )
            labels["scheduled"].configure(text=str(scheduled_today))
 
        if history_rows is not None:
            def visit_day(appt):
                when = appt["checked_in_at"] or appt["scheduled"]
                return when.date()
 
            completed_today = sum(
                1 for a in _rows_to_appointments(history_rows)
                if a["status"] == "Completed" and visit_day(a) == today
            )
            labels["completed"].configure(text=str(completed_today))
 
        try:
            names = self.room_controller.room_names_for([a["id"] for a in consulting])
        except AppointMedError:
            names = {}
        room = next((names[a["id"]] for a in consulting if a["id"] in names), None)
        self.doctor_room_value.configure(text=room or "—")

    def refresh_doctor_page(self):
        """Called after a profile save so this page shows the new details."""
        self.doctor_name_label.configure(text=self.doctor.full_name)
        self.doctor_username_label.configure(text="@" + getattr(self.doctor, "username", ""))
        self.doctor_spec_badge.configure(
            text=getattr(self.doctor, "specialization", "General Practice")
        )
        self.doctor_avatar.configure(
            image=render_avatar(self.avatar_bytes, self.doctor.full_name, 72, bg=AVATAR_BG)
        )

    # ---------------------------------------------------------------
    # ROOM PAGE — live room status from the database
    # ---------------------------------------------------------------
    def build_room_page(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            page, text="Room", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            page, text="Where your patient is now, and the status of every room in the clinic",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # Everything below the title is (re)drawn by load_room_status().
        self._room_drawn = None
        self.room_body = _ScrollList(page, fg_color="transparent")
        self.room_body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def load_room_status(self):
        """Redraw the Room page from the database:
          * MY CURRENT ROOM - the room of the patient being consulted now
          * ALL CLINIC ROOMS - Available / Occupied / Maintenance, with a
            button to put a free room into (or out of) maintenance.
        Skips the redraw if nothing changed."""
        try:
            rooms = self.room_controller.list_rooms()
        except AppointMedError:
            return
        try:
            consulting = _rows_to_appointments(
                self.appointment_controller.get_consulting_for_doctor(self.doctor.user_id)
            )
            names = self.room_controller.room_names_for([a["id"] for a in consulting])
        except AppointMedError:
            consulting, names = [], {}

        signature = (
            tuple((r["id"], r["status"], r["patient"]) for r in rooms),
            tuple((a["id"], names.get(a["id"])) for a in consulting),
        )
        if signature == self._room_drawn:
            return
        self._room_drawn = signature

        body = self.room_body
        scroll_at = body.scroll_position()
        body.clear()

        # --- my current room ---
        body.add_day_heading("MY CURRENT ROOM")
        box = ctk.CTkFrame(body, corner_radius=10)
        box.pack(fill="x", pady=4)
        if consulting:
            appt = consulting[0]
            title = names.get(appt["id"], "No room assigned")
            text = "Now consulting: " + appt["patient"]
        else:
            title = "No patient inside"
            text = "Start a consultation from the Appointments page."
        ctk.CTkLabel(
            box, text=title, anchor="w", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(fill="x", padx=20, pady=(16, 2))
        ctk.CTkLabel(
            box, text=text, anchor="w",
            font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
        ).pack(fill="x", padx=20, pady=(0, 16))

        # --- all rooms ---
        body.add_day_heading("ALL CLINIC ROOMS")
        for room in rooms:
            card = ctk.CTkFrame(body, corner_radius=10)
            card.pack(fill="x", pady=6)

            ctk.CTkLabel(
                card, text="🚪", font=ctk.CTkFont(size=22), width=60
            ).pack(side="left", padx=(12, 0), pady=14)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=14)
            ctk.CTkLabel(
                info, text=room["name"], anchor="w",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(fill="x")
            if room["status"] == "Occupied":
                sub = "Consulting: " + room["patient"]
            elif room["status"] == "Maintenance":
                sub = "Closed - cannot be assigned to appointments"
            else:
                sub = "Free - can be assigned to appointments"
            ctk.CTkLabel(
                info, text=sub, anchor="w",
                font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
            ).pack(fill="x")

            # side="right": the badge is packed first so it sits at the far
            # edge, with the maintenance button just to its left.
            bg, fg = ROOM_STATUS_COLORS[room["status"]]
            ctk.CTkLabel(
                card, text=room["status"], fg_color=bg, text_color=fg,
                corner_radius=8, width=100, height=26,
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side="right", padx=16)

            if room["status"] == "Maintenance":
                button_text, color, hover = "Mark available", COMPLETE_BG, COMPLETE_HOVER
            else:
                button_text, color, hover = "Set maintenance", CANCEL_BG, CANCEL_HOVER
            ctk.CTkButton(
                card, text=button_text, width=120, height=28,
                fg_color=color, hover_color=hover,
                # A room with a patient in it can't be closed.
                state="disabled" if room["status"] == "Occupied" else "normal",
                command=lambda r=room: self.toggle_maintenance(r)
            ).pack(side="right", padx=(8, 0))

        body.restore_scroll(scroll_at)

    def toggle_maintenance(self, room):
        """Put a free room into maintenance, or bring it back."""
        turning_on = room["status"] != "Maintenance"
        try:
            self.room_controller.set_maintenance(room["id"], turning_on, self.doctor.user_id)
        except AppointMedError as e:
            messagebox.showerror("Error", str(e))
            return
        self._room_drawn = None   # force a redraw
        self.load_room_status()

    def build_notifications_page(self, parent):
        """Notifications tab — alerts and reminders. Not built yet."""
        return self.build_placeholder_page(parent, "Notifications window")

    def build_invoice_page(self, parent):
        return InvoicePage(parent, self.doctor)  

   def build_history_page(self, parent):
        """History tab: shared searchable, paged history table."""
        self.history_board = HistoryView(parent, self.doctor)
        return self.history_board

        ctk.CTkLabel(
            page, text="History", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            page, text="Completed and cancelled appointments, most recent first",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        self.history_board = DoctorHistoryBoard(
            page, self.appointment_controller, self.doctor.user_id
        )
        self.history_board.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    # def build_settings_page(self, parent):
    #         """Settings tab: shared preferences form."""
    #         return SettingsView(
    #             parent, self.doctor,
    #             on_saved=lambda: self.history_board.reload_settings()
    #         )         ERROR HUHUHHUHU

    # ---------------------------------------------------------------
    # HELP PAGE — FAQ (collapsible) + support contact
    # ---------------------------------------------------------------
    def build_help_page(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            page, text="Help & FAQ", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            page, text="Click a question to see the answer",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 12))

        body = _ScrollList(page, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        for section_title, items in FAQ_SECTIONS:
            body.add_day_heading(section_title)
            for question, answer in items:
                _FAQItem(body, question, answer).pack(fill="x", pady=4)

        body.add_day_heading("STILL NEED HELP?")
        contact = ctk.CTkFrame(body, corner_radius=10)
        contact.pack(fill="x", pady=4)
        ctk.CTkLabel(
            contact, text=SUPPORT_CONTACT, anchor="w", font=ctk.CTkFont(size=13)
        ).pack(fill="x", padx=20, pady=16)

        return page

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
        Records the new page, shows it, and re-highlights the sidebar.
        Pages that show database data are refreshed as they are opened."""
        self.current_view = key
        self.show_page(key)
        self.highlight_active_button()
        if key == "history":
            # Someone else (or another window) may have completed
            # appointments since it was last drawn.
            self.load_history()
        elif key == "doctor":
            self.load_doctor_stats()
        elif key == "room":
            self.load_room_status()

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
    # The drawing and the database calls live in the board/calendar classes
    # (sections 1B-1D above); this section just tells them when to refresh.
    #
    #   load_appointments()     board + calendar (+ the panel's date list)
    #   refresh_linked_pages()  History + Doctor numbers + Room page
    #   refresh_all()           both of the above (Refresh button, start-up,
    #                           the 20-second timer)
    #   on_board_change()       after a Check in / Consulting / Complete /
    #                           Cancel press on the board
    # ===================================================================
    def load_appointments(self):
        """Redraw the pending board and the calendar. (The calendar also
        refreshes the panel's "Selected date" list.)"""
        self.board.refresh()
        self.calendar_panel.refresh()

    def load_history(self):
        """Redraw the History page."""
        self.history_board.refresh()

    def refresh_linked_pages(self):
        """Everything that depends on appointment/room data but isn't the
        board itself. This is what keeps the Doctor page's numbers and the
        Room page in step with the Appointments page."""
        self.load_history()
        self.load_doctor_stats()
        self.load_room_status()

    def refresh_all(self):
        self.load_appointments()
        self.refresh_linked_pages()
        self.last_updated_label.configure(
            text="Updated " + format_time(datetime.now())
        )

    def on_board_change(self):
        """The board has already redrawn itself; update the rest."""
        self.calendar_panel.refresh()
        self.refresh_linked_pages()

    def schedule_auto_refresh(self):
        """Queue the next automatic reload."""
        self.after(self.AUTO_REFRESH_MS, self.auto_refresh)

    def auto_refresh(self):
        """Reload everything, then queue the next reload. A failure is
        printed instead of stopping the timer, so one bad refresh can
        never freeze the dashboard for good."""
        if not self.winfo_exists():
            return
        try:
            self.refresh_all()
        except Exception as error:
            print("[Doctor dashboard] auto-refresh failed: " + repr(error))
        self.schedule_auto_refresh()


# Lets you run this file on its own (python -m views.doctor.doctor_dashboard)
# with a fake doctor, instead of logging in every time you tweak the layout.
if __name__ == "__main__":
    class FakeDoctor:
        user_id = 1
        username = "jdiaz"
        full_name = "Dr. Juan Diaz"
        specialization = "Pediatrics"

        def dashboard_title(self):
            return "Dr. Juan Diaz — Pediatrics"

    DoctorDashboard(FakeDoctor()).mainloop()