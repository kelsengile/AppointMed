"""
Admin dashboard — built with CustomTkinter.
Lists every Doctor/Nurse/Admin account, and lets the admin add new
ones, including assigning a nurse to a doctor.

This version adds a collapsible, animated side panel (like the
"Modern Sidebar" reference image) with User / Server / Settings / Help
navigation buttons that swap the content shown on the right.
"""

import time
import customtkinter as ctk
from tkinter import messagebox

from controllers.user_controller import UserController
from utils.exceptions import AppointMedError

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

ROLE_COLORS = {
    "doctor": ("#E3F0FF", "#2B6CB0"),
    "nurse": ("#F3E8FF", "#6B46C1"),
    "admin": ("#FBE7E7", "#C53030"),
    "pharmacist": ("#FBE7E7", "#30C549"),
}

# ---------------------------------------------------------------------------
# NAV_ITEMS drives the whole sidebar: every button, its icon, and which
# "page" it should reveal. Add/remove a dict here and the sidebar updates
# itself automatically — you never have to touch build_sidebar() again.
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    {"key": "users",    "icon": "👤", "label": "Users",    "position": "top"},
    {"key": "server",   "icon": "🖥", "label": "Server",   "position": "top"},
    {"key": "settings", "icon": "⚙",  "label": "Settings", "position": "bottom"},
    {"key": "help",     "icon": "❓", "label": "Help",     "position": "bottom"},
]


class AdminDashboard(ctk.CTk):
    # Pixel widths the sidebar animates between.
    SIDEBAR_EXPANDED_WIDTH = 210
    SIDEBAR_COLLAPSED_WIDTH = 64
    # Instead of moving a fixed number of pixels per tick (which looks
    # jerky), the animation now runs for a fixed DURATION and recomputes
    # the exact width needed at each point in time, eased with
    # ease-out-cubic (starts fast, glides to a gentle stop). FRAME_MS is
    # just how often we redraw — small = smoother.
    ANIMATION_DURATION_S = 0.32
    ANIMATION_FRAME_MS = 8

    def __init__(self, admin):
        super().__init__()
        self.admin = admin
        self.user_controller = UserController()

        # --- new state used by the sidebar ---
        self.sidebar_expanded = True     # is the panel currently open?
        self.current_view = "users"      # which page is on screen right now

        self.title(admin.dashboard_title())
        self.geometry("1100x680")
        self.build_ui()
        self.load_users()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def build_ui(self):
        # `body` is just a plain container that holds the sidebar on the
        # left and the content area on the right, side by side.
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
        # pack_propagate(False) is the key line that makes the animation
        # possible: normally a frame shrinks/grows to fit its children,
        # which would fight against us resizing it by hand. This locks
        # the frame's width to whatever we set with .configure(width=...).
        self.sidebar.pack_propagate(False)

        # --- hamburger toggle button ---
        toggle_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        toggle_row.pack(fill="x", padx=8, pady=(16, 12))
        self.toggle_btn = ctk.CTkButton(
            toggle_row, text="✕", width=36, height=36,
            fg_color="transparent", hover_color="#2A3040",
            font=ctk.CTkFont(size=16),
            command=self.toggle_sidebar
        )
        self.toggle_btn.pack(side="left")

        # --- user profile block (sits right under the hamburger,
        #     like the logo/name row in the reference screenshot) ---
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.profile_frame.pack(fill="x", padx=8, pady=(0, 20))

        # Blank placeholder avatar: just a plain circle, no initials/photo
        # yet. Swap this out later for a real picture with something like:
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
            text=getattr(self.admin, "full_name", "Admin"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white", anchor="w"
        )
        self.profile_name_label.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # === NEW: make the whole profile block clickable ===============
        # We want clicking anywhere on the avatar/name row (not just a button)
        # to open the account profile. CTkFrame/CTkLabel don't
        # have a `command=` option like CTkButton does, so instead we
        # bind the raw "<Button-1>" (left click) event on each of the
        # three widgets that make up the row: the frame itself, the
        # avatar circle, and the name label. That way it doesn't matter
        # which part the admin actually clicks on.
        clickable_widgets = (self.profile_frame, self.profile_avatar, self.profile_name_label)
        for widget in clickable_widgets:
            # CHANGED: instead of opening a separate popup window, this
            # now calls switch_view("profile") — the exact same routing
            # used by the sidebar nav buttons — so the profile content
            # swaps in on the right-hand side like Users/Server/etc.
            widget.bind("<Button-1>", lambda e: self.switch_view("profile"))
            # Swap the mouse cursor to a "hand" pointer on hover so it's
            # visually obvious the row is clickable, and restore it when
            # the mouse leaves. This is the same affordance a normal
            # button gives you "for free".
            widget.bind("<Enter>", self._on_profile_hover_enter)
            widget.bind("<Leave>", self._on_profile_hover_leave)
        # =================================================================

        # --- navigation buttons, built from NAV_ITEMS ---
        # Items are split into a "top" group (Users, Server) and a
        # "bottom" group (Settings, Help) so Settings/Help can be pinned
        # to the very bottom of the sidebar, like "Sign out" in the
        # reference video.
        self.nav_buttons = {}
        top_items = [i for i in NAV_ITEMS if i["position"] == "top"]
        bottom_items = [i for i in NAV_ITEMS if i["position"] == "bottom"]

        for item in top_items:
            self._make_nav_button(item).pack(fill="x", padx=8, pady=2, side="top")

        # Packing the bottom group in REVERSE with side="bottom" is what
        # pins them to the floor of the sidebar while keeping their
        # on-screen order the same as in NAV_ITEMS (Settings above Help).
        # Tkinter's pack() stacks side="bottom" widgets from the floor
        # upward, so the first one packed ends up lowest.
        for item in reversed(bottom_items):
            self._make_nav_button(item).pack(fill="x", padx=8, pady=2, side="bottom")

        self.highlight_active_button()

    def _make_nav_button(self, item):
        """Creates one sidebar nav button and registers it in
        self.nav_buttons so switch_view()/highlight_active_button()/
        _update_sidebar_labels() can all find it by key."""
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"{item['icon']}   {item['label']}",
            anchor="w", height=40,
            fg_color="transparent", hover_color="#2A3040",
            text_color="white", font=ctk.CTkFont(size=13),
            # default-arg trick (k=item["key"]) so each lambda
            # captures its OWN key instead of the last loop value
            command=lambda k=item["key"]: self.switch_view(k)
        )
        self.nav_buttons[item["key"]] = btn
        return btn

    # === NEW: profile block hover + click handlers ======================
    def _on_profile_hover_enter(self, event=None):
        """Mouse entered the profile row: show a hand cursor and give
        the row a subtle highlight, same hover_color used by the nav
        buttons, so it reads as one consistent, clickable family."""
        self.profile_frame.configure(fg_color="#2A3040")
        self.profile_frame.configure(cursor="hand2")
        self.profile_avatar.configure(cursor="hand2")
        self.profile_name_label.configure(cursor="hand2")

    def _on_profile_hover_leave(self, event=None):
        """Mouse left the profile row: undo the hover highlight."""
        self.profile_frame.configure(fg_color="transparent")

    # (open_profile_popup was removed — the profile is now a normal page
    # inside the content area, built by build_profile_page() below, and
    # shown the same way any other sidebar page is shown.)
    # =====================================================================

    # ------------------------------------------------------------------
    # SIDEBAR ANIMATION
    # ------------------------------------------------------------------
    def toggle_sidebar(self):
        """Called by the hamburger button. Decides the target width and
        kicks off the eased animation toward it."""
        collapsing = self.sidebar_expanded  # True if we're about to close it
        start_width = self.sidebar.winfo_width()
        target_width = self.SIDEBAR_COLLAPSED_WIDTH if collapsing else self.SIDEBAR_EXPANDED_WIDTH
        self.sidebar_expanded = not self.sidebar_expanded

        # Morph the hamburger into an X (and back) the instant the click
        # happens — it's a fixed-width button so there's no squish risk,
        # and reacting immediately makes the toggle feel responsive even
        # though the panel itself takes a moment to glide open/closed.
        self.toggle_btn.configure(text="✕" if self.sidebar_expanded else "☰")

        if collapsing:
            # This is the fix for the "distorting" look: switch every
            # button to icon-only text RIGHT NOW, before the frame even
            # starts shrinking. That way the label never has to get
            # squeezed/clipped mid-slide — it's already short before the
            # width changes. (When *expanding*, we do the opposite: wait
            # until the frame has fully reached its final width before
            # switching back to icon+label text — see the end of
            # _animate_sidebar below.)
            self._set_sidebar_labels(expanded=False)

        self._animate_sidebar(
            start_width=start_width,
            target_width=target_width,
            start_time=time.perf_counter(),
            collapsing=collapsing,
        )

    def _animate_sidebar(self, start_width, target_width, start_time, collapsing):
        """Runs every ANIMATION_FRAME_MS milliseconds for a fixed total
        duration (ANIMATION_DURATION_S). Rather than moving a constant
        number of pixels each tick (which is what caused the choppy,
        "distorting" motion before), we look at how much time has
        actually elapsed and compute exactly where the sidebar should be
        *right now* on an ease-in-out curve. This keeps the motion smooth
        and consistent no matter how fast/slow the machine renders each
        frame."""
        elapsed = time.perf_counter() - start_time
        progress = min(elapsed / self.ANIMATION_DURATION_S, 1.0)  # 0.0 -> 1.0
        eased = self._ease_in_out_cubic(progress)

        new_width = round(start_width + (target_width - start_width) * eased)
        self.sidebar.configure(width=new_width)

        if progress < 1.0:
            self.after(
                self.ANIMATION_FRAME_MS,
                lambda: self._animate_sidebar(start_width, target_width, start_time, collapsing)
            )
            return

        # Animation finished — snap exactly onto the target width so we
        # never end up 1px off from rounding, then reveal full labels
        # again if we just finished expanding.
        self.sidebar.configure(width=target_width)
        if not collapsing:
            self._set_sidebar_labels(expanded=True)

    @staticmethod
    def _ease_in_out_cubic(t):
        """A symmetric 'ease-in-out' curve: gentle acceleration off the
        start, then gentle deceleration into the stop, rather than
        moving at a constant speed the whole way (or only easing at one
        end). This is the curve most "smooth" UI sidebar animations use,
        and it's what removes the last bit of mechanical/jarring feel."""
        if t < 0.5:
            return 4 * t ** 3
        return 1 - ((-2 * t + 2) ** 3) / 2

    def _set_sidebar_labels(self, expanded: bool):
        """When collapsed, buttons show icon-only and the profile name
        is hidden (only the round avatar placeholder remains) so nothing
        gets clipped. When expanded, full labels come back."""
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

        # Every nav button maps to one "page" (a full-size frame). All
        # pages are stacked on top of each other with place(), and
        # tkraise() is used to bring the right one to the front — this
        # is the simplest way to fake page-routing in plain Tkinter.
        self.pages = {
            "users": self.build_users_page(self.content_frame),
            "server": self.build_placeholder_page(self.content_frame, "Server window"),
            "settings": self.build_placeholder_page(self.content_frame, "Settings window"),
            "help": self.build_placeholder_page(self.content_frame, "Help window"),
            # NEW: "profile" isn't a sidebar nav button (it's not in
            # NAV_ITEMS), but it's routed to exactly the same way — it's
            # just another entry in this pages dict, raised with
            # tkraise() when the profile row up in the sidebar is clicked.
            "profile": self.build_profile_page(self.content_frame),
        }
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.current_view)

    def build_users_page(self, parent):
        """This is your original dashboard content (header + list),
        just moved into its own frame so it can be one page among several."""
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
            header, text="Refresh", width=90, fg_color="gray60",
            command=self.load_users
        ).pack(side="right")

        ctk.CTkLabel(
            page, text="User accounts", font=ctk.CTkFont(size=13), text_color="gray50"
        ).pack(anchor="w", padx=24, pady=(0, 16))

        self.list_frame = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        return page

    def build_profile_page(self, parent):
        """NEW: "My Account" page. Shown in the main content area (same
        spot as Users/Server/Settings/Help) when the admin clicks their
        avatar/name in the sidebar, instead of popping up a separate
        window. Replace the placeholder fields below with real
        edit-profile widgets (change password, etc.) whenever you're
        ready to make this functional."""
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
            text_col, text=getattr(self.admin, "full_name", "Admin"),
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            text_col, text="@" + getattr(self.admin, "username", "admin"),
            font=ctk.CTkFont(size=12), text_color="gray50", anchor="w"
        ).pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(
            text_col, text="Administrator",
            fg_color=ROLE_COLORS["admin"][0], text_color=ROLE_COLORS["admin"][1],
            corner_radius=8, font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", pady=(8, 0), ipadx=8, ipady=2)

        return page

    def build_placeholder_page(self, parent, text):
        """Server / Settings / Help don't have real functionality yet,
        so each just shows a big centered label confirming which button
        was pressed. Replace the label with real widgets later."""
        page = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(
            page, text=text, font=ctk.CTkFont(size=24, weight="bold"),
            text_color="gray30"
        ).pack(expand=True)
        return page

    def show_page(self, key):
        self.pages[key].tkraise()

    def switch_view(self, key):
        """Wired to every nav button's command=. Updates which page is
        showing and re-highlights the active button."""
        self.current_view = key
        self.show_page(key)
        self.highlight_active_button()

    def highlight_active_button(self):
        for key, btn in self.nav_buttons.items():
            btn.configure(fg_color="#2B6CB0" if key == self.current_view else "transparent")

    # ------------------------------------------------------------------
    # USER LIST (unchanged logic, just re-hooked to the new list_frame)
    # ------------------------------------------------------------------
    def clear_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def load_users(self):
        self.clear_list()
        try:
            users = self.user_controller.get_all_users()
        except AppointMedError:
            users = []

        if not users:
            ctk.CTkLabel(self.list_frame, text="No users found.", text_color="gray50").pack(pady=40)
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

        subtitle = "@" + user["username"]
        if user["role"] == "doctor" and user.get("specialization"):
            subtitle = subtitle + " · " + user["specialization"]
        if user["role"] == "nurse" and user.get("assigned_doctor_id"):
            subtitle = subtitle + " · assigned to doctor #" + str(user["assigned_doctor_id"])
        ctk.CTkLabel(
            info, text=subtitle, font=ctk.CTkFont(size=12), text_color="gray50", anchor="w"
        ).pack(fill="x")

        colors = ROLE_COLORS.get(user["role"], ROLE_COLORS["admin"])
        bg = colors[0]
        fg = colors[1]
        ctk.CTkLabel(
            row, text=user["role"].capitalize(), fg_color=bg, text_color=fg,
            corner_radius=8, width=80, height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=(8, 16))

        ctk.CTkButton(
            row, text="Delete", width=70, height=26,
            fg_color="#C53030", hover_color="#9B2C2C",
            command=lambda u=user: self.delete_user(u)
        ).pack(side="right", padx=(8, 0))

    def delete_user(self, user):
        confirmed = messagebox.askyesno("Confirm", "Delete account for " + user["full_name"] + "?")
        if not confirmed:
            return
        try:
            self.user_controller.delete_user(user["id"])
        except AppointMedError as e:
            messagebox.showerror("Error", str(e))
        self.load_users()

    def open_add_form(self):
        form = ctk.CTkToplevel(self)
        form.title("Add User")
        form.geometry("380x560")
        form.grab_set()

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

        status_label = ctk.CTkLabel(form, text="", text_color="#d64545")
        status_label.pack(pady=(4, 0))

        def submit():
            try:
                role = role_var.get()

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
                status_label.configure(text=str(e))
            except ValueError:
                status_label.configure(text="Assigned doctor ID must be a number.")

        ctk.CTkButton(form, text="Create account", command=submit).pack(pady=24)

    def labeled_entry(self, parent, label_text, show=None):
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(fill="x", padx=30, pady=(10, 2))
        if show:
            entry = ctk.CTkEntry(parent, width=300, show=show)
        else:
            entry = ctk.CTkEntry(parent, width=300)
        entry.pack(padx=30)
        return entry