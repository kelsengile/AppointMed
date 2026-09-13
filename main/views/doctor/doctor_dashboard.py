"""
Doctor's dashboard — built with CustomTkinter.
Adds the same collapsible, animated sidebar used in the admin dashboard.
Only the "Appointments" page has real content right now (today's
schedule as cards with a status badge and a "Complete" button) — the
rest of the nav items are placeholders ready for you to build out.
"""

import time
import customtkinter as ctk
from datetime import date

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
    {"id": 3, "time": "10:15 AM", "patient": "Kian Ang", "reason": "Vaccination", "status": "Scheduled"},
]

# ---------------------------------------------------------------------------
# NAV_ITEMS drives the whole sidebar: every button, its icon, and where it
# sits. "top" and "middle" both stack from the top of the panel (in the
# order they appear in this list); "bottom" items are pinned to the floor
# of the sidebar. Add/remove a dict here and the sidebar updates itself —
# you never have to touch build_sidebar() again.
# ---------------------------------------------------------------------------
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


class DoctorDashboard(ctk.CTk):
    # Pixel widths the sidebar animates between.
    SIDEBAR_EXPANDED_WIDTH = 210
    SIDEBAR_COLLAPSED_WIDTH = 64
    # The animation runs for a fixed DURATION and recomputes the exact
    # width needed at each point in time (eased with ease-in-out-cubic),
    # instead of moving a constant number of pixels per tick. FRAME_MS is
    # just how often we redraw — small = smoother.
    ANIMATION_DURATION_S = 0.32
    ANIMATION_FRAME_MS = 8

    def __init__(self, doctor):
        super().__init__()
        self.doctor = doctor
        self.appointment_controller = AppointmentController()

        # --- state used by the sidebar ---
        self.sidebar_expanded = True         # is the panel currently open?
        self.current_view = "appointments"   # which page is on screen right now

        self.title(doctor.dashboard_title())
        self.geometry("1100x680")
        self.build_ui()
        self.load_appointments()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def build_ui(self):
        # `body` holds the sidebar on the left and the content area on
        # the right, side by side.
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

        self.build_sidebar(self.body)
        self.build_content_area(self.body)

    # ------------------------------------------------------------------
    # SIDEBAR
    # ------------------------------------------------------------------
    def build_sidebar(self, parent):
        self.sidebar = ctk.CTkFrame(
            parent, width=self.SIDEBAR_EXPANDED_WIDTH,
            corner_radius=0, fg_color="#1A1F2B"
        )
        self.sidebar.pack(side="left", fill="y")
        # pack_propagate(False) locks the frame's width to whatever we
        # set with .configure(width=...) — without it, the frame would
        # just shrink/grow to fit its children and fight the animation.
        self.sidebar.pack_propagate(False)

        # --- hamburger / close toggle button ---
        toggle_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        toggle_row.pack(fill="x", padx=8, pady=(16, 12))
        self.toggle_btn = ctk.CTkButton(
            toggle_row, text="✕", width=36, height=36,
            fg_color="transparent", hover_color="#2A3040",
            font=ctk.CTkFont(size=16),
            command=self.toggle_sidebar
        )
        self.toggle_btn.pack(side="left")

        # --- profile block (blank placeholder avatar for now) ---
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(fill="x", padx=8, pady=(0, 20))

        # Plain circle, no photo yet. Swap in a real picture later with:
        #   from PIL import Image
        #   img = ctk.CTkImage(Image.open("avatar.png"), size=(40, 40))
        #   self.profile_avatar.configure(image=img, text="")
        self.profile_avatar = ctk.CTkLabel(
            self.profile_frame, text="", width=40, height=40,
            corner_radius=20, fg_color="#3A4152"
        )
        self.profile_avatar.pack(side="left")

        self.profile_name_label = ctk.CTkLabel(
            self.profile_frame,
            text=getattr(self.doctor, "full_name", "Doctor"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white", anchor="w"
        )
        self.profile_name_label.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # === NEW: make the whole profile block clickable ===============
        # Same pattern as the admin/nurse dashboards: CTkFrame/CTkLabel
        # don't have a `command=`, so we bind the raw "<Button-1>" (left click)
        # on the frame, the avatar, and the name label — that way
        # it doesn't matter which part of the row is actually clicked.
        # The click routes to switch_view("profile"), which swaps in the
        # profile page in the main content area, exactly like clicking
        # Appointments/Doctor/Room/etc. does — no separate popup window.
        clickable_widgets = (self.profile_frame, self.profile_avatar, self.profile_name_label)
        for widget in clickable_widgets:
            widget.bind("<Button-1>", lambda e: self.switch_view("profile"))
            # Hand cursor + hover highlight on enter/leave, matching the
            # nav buttons' hover_color, so the row visually reads as
            # clickable just like they do.
            widget.bind("<Enter>", self._on_profile_hover_enter)
            widget.bind("<Leave>", self._on_profile_hover_leave)
        # =================================================================

        # --- navigation buttons, built from NAV_ITEMS ---
        # "top" and "middle" items both stack from the top (in order);
        # "bottom" items get pinned to the floor of the sidebar.
        self.nav_buttons = {}
        stacked_items = [i for i in NAV_ITEMS if i["position"] in ("top", "middle")]
        bottom_items = [i for i in NAV_ITEMS if i["position"] == "bottom"]

        for item in stacked_items:
            self._make_nav_button(item).pack(fill="x", padx=8, pady=2, side="top")

        # Packing the bottom group in REVERSE with side="bottom" pins
        # them to the floor while keeping their on-screen order the same
        # as in NAV_ITEMS (Settings above Help). Tkinter's pack() stacks
        # side="bottom" widgets from the floor upward, so the first one
        # packed ends up lowest.
        for item in reversed(bottom_items):
            self._make_nav_button(item).pack(fill="x", padx=8, pady=2, side="bottom")

        self.highlight_active_button()

    def _make_nav_button(self, item):
        """Creates one sidebar nav button and registers it in
        self.nav_buttons so switch_view()/highlight_active_button()/
        _set_sidebar_labels() can all find it by key."""
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"{item['icon']}   {item['label']}",
            anchor="w", height=40,
            fg_color="transparent", hover_color="#2A3040",
            text_color="white", font=ctk.CTkFont(size=13),
            # default-arg trick (k=item["key"]) so each lambda captures
            # its OWN key instead of the last loop value
            command=lambda k=item["key"]: self.switch_view(k)
        )
        self.nav_buttons[item["key"]] = btn
        return btn

    # === NEW: profile block hover handlers ===============================
    def _on_profile_hover_enter(self, event=None):
        """Mouse entered the profile row: show a hand cursor and give
        the row the same subtle highlight the nav buttons use on hover,
        so it reads as one consistent, clickable family."""
        self.profile_frame.configure(fg_color="#2A3040")
        self.profile_frame.configure(cursor="hand2")
        self.profile_avatar.configure(cursor="hand2")
        self.profile_name_label.configure(cursor="hand2")

    def _on_profile_hover_leave(self, event=None):
        """Mouse left the profile row: undo the hover highlight."""
        self.profile_frame.configure(fg_color="transparent")
    # =====================================================================

    # ------------------------------------------------------------------
    # SIDEBAR ANIMATION
    # ------------------------------------------------------------------
    def toggle_sidebar(self):
        """Called by the hamburger/X button. Decides the target width
        and kicks off the eased animation toward it."""
        collapsing = self.sidebar_expanded  # True if we're about to close it
        start_width = self.sidebar.winfo_width()
        target_width = self.SIDEBAR_COLLAPSED_WIDTH if collapsing else self.SIDEBAR_EXPANDED_WIDTH
        self.sidebar_expanded = not self.sidebar_expanded

        # Morph the icon immediately — it's a fixed-width button so
        # there's no squish risk, and reacting right away makes the
        # toggle feel responsive even though the panel itself glides.
        self.toggle_btn.configure(text="✕" if self.sidebar_expanded else "☰")

        if collapsing:
            # Switch every button to icon-only text RIGHT NOW, before
            # the frame starts shrinking, so labels never get squeezed
            # or clipped mid-slide.
            self._set_sidebar_labels(expanded=False)

        self._animate_sidebar(
            start_width=start_width,
            target_width=target_width,
            start_time=time.perf_counter(),
            collapsing=collapsing,
        )

    def _animate_sidebar(self, start_width, target_width, start_time, collapsing):
        """Runs every ANIMATION_FRAME_MS for a fixed total duration,
        computing exactly where the sidebar should be *right now* on an
        ease-in-out curve. This keeps the motion smooth and consistent
        no matter how fast/slow the machine renders each frame."""
        elapsed = time.perf_counter() - start_time
        progress = min(elapsed / self.ANIMATION_DURATION_S, 1.0)
        eased = self._ease_in_out_cubic(progress)

        new_width = round(start_width + (target_width - start_width) * eased)
        self.sidebar.configure(width=new_width)

        if progress < 1.0:
            self.after(
                self.ANIMATION_FRAME_MS,
                lambda: self._animate_sidebar(start_width, target_width, start_time, collapsing)
            )
            return

        # Snap exactly onto the target width (avoids 1px rounding drift),
        # then reveal full labels again if we just finished expanding.
        self.sidebar.configure(width=target_width)
        if not collapsing:
            self._set_sidebar_labels(expanded=True)

    @staticmethod
    def _ease_in_out_cubic(t):
        """Gentle acceleration off the start, gentle deceleration into
        the stop — the curve behind most smooth UI slide animations."""
        if t < 0.5:
            return 4 * t ** 3
        return 1 - ((-2 * t + 2) ** 3) / 2

    def _set_sidebar_labels(self, expanded: bool):
        """When collapsed, buttons show icon-only and the profile name
        is hidden (only the round avatar placeholder remains). When
        expanded, full labels come back."""
        for item in NAV_ITEMS:
            btn = self.nav_buttons[item["key"]]
            if expanded:
                btn.configure(text=f"{item['icon']}   {item['label']}", anchor="w")
            else:
                btn.configure(text=item["icon"], anchor="center")

        if expanded:
            self.profile_name_label.pack(side="left", padx=(10, 0), fill="x", expand=True)
        else:
            self.profile_name_label.pack_forget()

    # ------------------------------------------------------------------
    # CONTENT AREA / PAGE SWITCHING
    # ------------------------------------------------------------------
    def build_content_area(self, parent):
        self.content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Every nav button maps to one "page". All pages are stacked on
        # top of each other with place(), and tkraise() brings the right
        # one to the front — the simplest way to fake page-routing in
        # plain Tkinter.
        self.pages = {"appointments": self.build_appointments_page(self.content_frame)}
        for item in NAV_ITEMS:
            if item["key"] == "appointments":
                continue
            self.pages[item["key"]] = self.build_placeholder_page(
                self.content_frame, f"{item['label']} window"
            )

        # NEW: "profile" isn't a sidebar nav button (it's not in
        # NAV_ITEMS), but it's routed to exactly the same way — it's
        # just another entry in this pages dict, raised with tkraise()
        # when the profile row up in the sidebar is clicked.
        self.pages["profile"] = self.build_profile_page(self.content_frame)

        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.current_view)

    def build_appointments_page(self, parent):
        """Your original dashboard content (header + today's schedule),
        moved into its own page frame so it can be one page among several."""
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
            font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        self.list_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def build_profile_page(self, parent):
        """NEW: "My Account" page for the doctor. Shown in the main
        content area (same spot as Appointments/Doctor/Room/etc.) when
        the doctor clicks their avatar/name in the sidebar, instead of
        popping up a separate window. Replace the placeholder fields
        below with real edit-profile widgets whenever you're ready to
        make this functional."""
        page = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            header, text="My Account",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            page, text="Account details", font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        card = ctk.CTkFrame(page, corner_radius=10)
        card.pack(fill="x", padx=24)

        avatar_row = ctk.CTkFrame(card, fg_color="transparent")
        avatar_row.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            avatar_row, text="", width=64, height=64, corner_radius=32,
            fg_color="#3A4152"
        ).pack(side="left")

        text_col = ctk.CTkFrame(avatar_row, fg_color="transparent")
        text_col.pack(side="left", padx=(16, 0), fill="x", expand=True)

        ctk.CTkLabel(
            text_col, text=getattr(self.doctor, "full_name", "Doctor"),
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            text_col, text="@" + getattr(self.doctor, "username", "doctor"),
            font=ctk.CTkFont(size=12), text_color="gray50", anchor="w"
        ).pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(
            text_col, text="Doctor",
            fg_color="#E3F0FF", text_color="#2B6CB0",
            corner_radius=8, font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(8, 0), ipadx=8, ipady=2)

        specialization = getattr(self.doctor, "specialization", None)
        if specialization:
            ctk.CTkLabel(
                card, text="Specialization: " + specialization,
                font=ctk.CTkFont(size=12), text_color="gray50", anchor="w"
            ).pack(fill="x", padx=20, pady=(0, 20))
        else:
            # keeps the card's bottom padding consistent even when
            # there's no specialization to show
            ctk.CTkFrame(card, fg_color="transparent", height=4).pack(fill="x")

        return page

    def build_placeholder_page(self, parent, text):
        """Doctor / Room / Notifications / Invoice / History / Settings /
        Help don't have real functionality yet, so each just shows a big
        centered label confirming which button was pressed. Replace with
        real widgets later."""
        page = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(
            page, text=text, font=ctk.CTkFont(size=24, weight="bold"),
            text_color="gray30"
        ).pack(expand=True)
        return page

    def show_page(self, key):
        self.pages[key].tkraise()

    def switch_view(self, key):
        """Wired to every nav button's command= (and now the profile
        row too). Updates which page is showing and re-highlights the
        active button."""
        self.current_view = key
        self.show_page(key)
        self.highlight_active_button()

    def highlight_active_button(self):
        for key, btn in self.nav_buttons.items():
            btn.configure(fg_color="#2B6CB0" if key == self.current_view else "transparent")

    # ------------------------------------------------------------------
    # APPOINTMENTS LIST (unchanged logic, re-hooked to the new list_frame)
    # ------------------------------------------------------------------
    def clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def load_appointments(self):
        self.clear_list()
        try:
            rows = self.appointment_controller.get_schedule_for_doctor(
                self.doctor.user_id, date.today().isoformat()
            )
            appointments = []
            for r in rows:
                patient_name = r.get("patient_name")
                if not patient_name:
                    patient_name = "Patient #" + str(r["patient_id"])
                appointments.append({
                    "id": r["id"],
                    "time": r["scheduled_time"].strftime("%-I:%M %p"),
                    "patient": patient_name,
                    "reason": r["reason"],
                    "status": r["status"],
                })
        except AppointMedError:
            appointments = SAMPLE_APPOINTMENTS

        if not appointments:
            ctk.CTkLabel(
                self.list_frame, text="No appointments scheduled for today.",
                text_color="gray50"
            ).pack(pady=40)
            return

        for appt in appointments:
            self.add_appointment_card(appt)

    def add_appointment_card(self, appt):
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

        colors = STATUS_COLORS.get(appt["status"], STATUS_COLORS["Scheduled"])
        bg = colors[0]
        fg = colors[1]
        ctk.CTkLabel(
            card, text=appt["status"], fg_color=bg, text_color=fg,
            corner_radius=8, width=90, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        if appt["status"] != "Completed" and appt["status"] != "Cancelled":
            ctk.CTkButton(
                card, text="Complete", width=80, height=26,
                fg_color="#2F855A", hover_color="#276749",
                command=lambda a=appt: self.mark_completed(a)
            ).pack(side="right", padx=(8, 0))

    def mark_completed(self, appt):
        try:
            self.appointment_controller.update_status(appt["id"], "Completed")
        except AppointMedError:
            pass
        self.load_appointments()


if __name__ == "__main__":
    class FakeDoctor:
        user_id = 1
        full_name = "Dr. Juan Diaz"
        def dashboard_title(self):
            return "Dr. Juan Diaz — Pediatrics"

    DoctorDashboard(FakeDoctor()).mainloop()