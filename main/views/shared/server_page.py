"""
Server page - shared by the Admin, Doctor and Nurse dashboards.

Shows whether this device can reach the central MySQL database that every
device shares, and lets the user test the connection.

    Role     Can do
    -------  ----------------------------------------------------------
    Admin    view status, test, AND change + save the server settings
    Nurse    view status and test (settings are read-only)
    Doctor   view status and test (settings are read-only)

Use it from a dashboard like this:

    def build_server_page(self, parent):
        return ServerPage(parent, self.doctor)

Checking a server can take a few seconds when it is unreachable, so every
network call runs on a background thread and the result is handed back to
the screen through a queue (Tkinter widgets must only be touched from the
main thread). All database logic lives in ServerController.
"""

import queue
import threading
from datetime import datetime

import customtkinter as ctk

from controllers.server_controller import ServerController
from models.user import Admin
from utils.exceptions import AppointMedError

MUTED_TEXT = "gray50"
ERROR_TEXT = "#d64545"
SUCCESS_TEXT = "#2F855A"
WARNING_BG, WARNING_HOVER = "#D97706", "#B45309"
REFRESH_BG = "gray60"
POLL_MS = 100


class ServerPage(ctk.CTkFrame):

    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.controller = ServerController()
        self.can_edit = isinstance(user, Admin)

        self._results = queue.Queue()   # (callback, value) pairs from worker threads
        self._pending = 0               # background jobs still running
        self._poll_id = None

        self._build()
        self.refresh_status()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self):
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        header = ctk.CTkFrame(body, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            header, text="Server", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            header, text="Check status", width=110, fg_color=REFRESH_BG,
            command=self.refresh_status
        ).pack(side="right")

        ctk.CTkLabel(
            body, text="The central MySQL database that every AppointMed device shares.",
            font=ctk.CTkFont(size=13), text_color=MUTED_TEXT
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # --- status card ---
        status_card = ctk.CTkFrame(body, corner_radius=10)
        status_card.pack(fill="x", padx=24, pady=(0, 16))

        self.status_label = ctk.CTkLabel(
            status_card, text="●  Checking...", text_color=MUTED_TEXT,
            font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(16, 2))

        self.detail_label = ctk.CTkLabel(
            status_card, text="", text_color=MUTED_TEXT, anchor="w",
            justify="left", wraplength=700
        )
        self.detail_label.pack(fill="x", padx=20, pady=(0, 10))

        tiles = ctk.CTkFrame(status_card, fg_color="transparent")
        tiles.pack(fill="x", padx=20, pady=(0, 16))
        self.count_labels = {}
        for _table, label in ServerController.STAT_TABLES:
            tile = ctk.CTkFrame(tiles, corner_radius=8)
            tile.pack(side="left", fill="x", expand=True, padx=(0, 10))
            ctk.CTkLabel(
                tile, text=label, font=ctk.CTkFont(size=12), text_color=MUTED_TEXT
            ).pack(anchor="w", padx=12, pady=(8, 0))
            value = ctk.CTkLabel(tile, text="-", font=ctk.CTkFont(size=18, weight="bold"))
            value.pack(anchor="w", padx=12, pady=(0, 8))
            self.count_labels[label] = value

        # --- settings card ---
        card = ctk.CTkFrame(body, corner_radius=10)
        card.pack(fill="x", padx=24, pady=(0, 20))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            inner, text="Connection settings", anchor="w",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(fill="x", pady=(0, 10))

        current = self.controller.current_settings()
        self.host_entry = self._field(inner, "Server host (IP)", current["host"])
        self.port_entry = self._field(inner, "Port", str(current["port"]))
        self.user_entry = self._field(inner, "Database user", current["user"])
        self.password_entry = self._field(inner, "Password (leave blank to keep the current one)", "", show="*")
        # The schema is hard-wired to appointmed_db, so the name is shown but never editable.
        self.database_entry = self._field(inner, "Database name", current["database"])
        self.database_entry.configure(state="disabled")

        if not self.can_edit:
            for entry in (self.host_entry, self.port_entry, self.user_entry, self.password_entry):
                entry.configure(state="disabled")
            ctk.CTkLabel(
                inner, text="Only an administrator can change the server settings. "
                            "You can still test the connection.",
                text_color=MUTED_TEXT, anchor="w", justify="left", wraplength=620
            ).pack(fill="x", pady=(0, 10))

        self.feedback_label = ctk.CTkLabel(inner, text="", anchor="w", justify="left", wraplength=620)
        self.feedback_label.pack(fill="x", pady=(0, 10))

        buttons = ctk.CTkFrame(inner, fg_color="transparent")
        buttons.pack(fill="x")
        self.test_button = ctk.CTkButton(
            buttons, text="Test connection", width=140,
            fg_color=WARNING_BG, hover_color=WARNING_HOVER, command=self.test_connection
        )
        self.test_button.pack(side="left", padx=(0, 10))
        if self.can_edit:
            self.save_button = ctk.CTkButton(buttons, text="Save settings", width=140, command=self.save_settings)
            self.save_button.pack(side="left")
            ctk.CTkLabel(
                inner, text="Saving tests the new server first. If you switch to a different server, "
                            "log out and back in so your account is loaded from it.",
                text_color=MUTED_TEXT, anchor="w", justify="left", wraplength=620,
                font=ctk.CTkFont(size=11)
            ).pack(fill="x", pady=(10, 0))

    @staticmethod
    def _field(parent, label_text, value, show=None):
        ctk.CTkLabel(parent, text=label_text, anchor="w").pack(fill="x", pady=(0, 2))
        entry = ctk.CTkEntry(parent, width=320, show=show) if show else ctk.CTkEntry(parent, width=320)
        entry.pack(anchor="w", pady=(0, 12))
        if value:
            entry.insert(0, value)
        return entry

    # ------------------------------------------------------------------
    # Status card
    # ------------------------------------------------------------------
    def refresh_status(self):
        self.status_label.configure(text="●  Checking...", text_color=MUTED_TEXT)
        self.detail_label.configure(text="")
        self._background(self.controller.check_connection, self._show_status)

    def _show_status(self, result):
        stamp = "Last checked " + datetime.now().strftime("%H:%M:%S")
        if isinstance(result, Exception):
            result = {"ok": False, "error": str(result)}

        if result["ok"]:
            self.status_label.configure(text="●  Connected", text_color=SUCCESS_TEXT)
            self.detail_label.configure(
                text="Response " + str(result["latency_ms"]) + " ms  ·  MySQL "
                     + str(result["version"]) + "  ·  " + stamp
            )
            for label, widget in self.count_labels.items():
                total = result["counts"].get(label)
                widget.configure(text="-" if total is None else str(total))
        else:
            self.status_label.configure(text="●  Not connected", text_color=ERROR_TEXT)
            self.detail_label.configure(text=str(result["error"]) + "\n" + stamp)
            for widget in self.count_labels.values():
                widget.configure(text="-")

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def _form_overrides(self):
        """What is typed in the form, as settings to try. Blank password
        means 'keep the current one', so it is left out."""
        overrides = {
            "host": self.host_entry.get().strip(),
            "user": self.user_entry.get().strip(),
        }
        port_text = self.port_entry.get().strip()
        overrides["port"] = int(port_text)      # ValueError handled by the caller
        password = self.password_entry.get()
        if password:
            overrides["password"] = password
        return overrides

    def test_connection(self):
        try:
            overrides = self._form_overrides()
        except ValueError:
            self._feedback("Port must be a number, like 3306.", ERROR_TEXT)
            return
        self._feedback("Testing connection...", MUTED_TEXT)
        self.test_button.configure(state="disabled")
        self._background(lambda: self.controller.check_connection(overrides), self._after_test)

    def _after_test(self, result):
        self.test_button.configure(state="normal")
        if result["ok"]:
            self._feedback("Connection successful (" + str(result["latency_ms"]) + " ms).", SUCCESS_TEXT)
        else:
            self._feedback("Failed: " + str(result["error"]), ERROR_TEXT)

    def save_settings(self):
        self._feedback("Testing and saving...", MUTED_TEXT)
        self.save_button.configure(state="disabled")
        host, port = self.host_entry.get(), self.port_entry.get()
        user, password = self.user_entry.get(), self.password_entry.get()
        self._background(
            lambda: self.controller.apply_settings(host, port, user, password),
            self._after_save
        )

    def _after_save(self, result):
        self.save_button.configure(state="normal")
        if isinstance(result, AppointMedError):
            self._feedback(str(result), ERROR_TEXT)
            return
        if isinstance(result, Exception):
            self._feedback("Could not save: " + str(result), ERROR_TEXT)
            return
        self.password_entry.delete(0, "end")
        self._feedback("Settings saved. The app is now using this server.", SUCCESS_TEXT)
        self._show_status(result)

    def _feedback(self, text, color):
        self.feedback_label.configure(text=text, text_color=color)

    # ------------------------------------------------------------------
    # Background work (thread -> queue -> main thread)
    # ------------------------------------------------------------------
    def _background(self, work, callback):
        """Runs work() on a thread, then calls callback(value) on the Tk
        thread. If work() raises, the exception object itself is passed to
        the callback instead of a value."""
        def worker():
            try:
                value = work()
            except Exception as e:
                value = e
            self._results.put((callback, value))

        self._pending += 1
        threading.Thread(target=worker, daemon=True).start()
        if self._poll_id is None:
            self._poll_id = self.after(POLL_MS, self._poll)

    def _poll(self):
        self._poll_id = None
        try:
            while True:
                callback, value = self._results.get_nowait()
                self._pending -= 1
                callback(value)
        except queue.Empty:
            pass
        if self._pending > 0:
            self._poll_id = self.after(POLL_MS, self._poll)

    def destroy(self):
        if self._poll_id is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:
                pass
            self._poll_id = None
        super().destroy()
