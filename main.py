"""
MindConnect — Mental Health & Therapist Booking System
======================================================
Author   : Betty Brenda Wawira Kariuki  | Reg: 17/01880
Unit     : STU 3101 — Programming Project
University: KCA University
Supervisor: Mr. Martin Mukiri
Date     : June 2026
------------------------------------------------------
Stack    : Python 3.10+, Tkinter, SQLite (dev) / PostgreSQL (prod)
Run      : python main.py
"""

import tkinter as tk
from tkinter import ttk
import sys, os

# ── make imports work from any cwd ──────────────────
sys.path.insert(0, os.path.dirname(__file__))

from db.database   import Database
from db.seed       import seed_database
from views.login   import LoginView
from views.styles  import apply_theme
from services.reminder_scheduler import ReminderScheduler


class App(tk.Tk):
    """Root application window — single-window architecture with frame switching."""

    def __init__(self):
        super().__init__()
        self.title("MindConnect — Mental Health & Therapist Booking")
        self.geometry("1200x750")
        self.minsize(960, 620)
        self.configure(bg="#0D1F2D")

        # Centre on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1200) // 2
        y = (self.winfo_screenheight() - 750)  // 2
        self.geometry(f"1200x750+{x}+{y}")

        apply_theme(self)

        # ── database ────────────────────────────────
        self.db = Database()
        seed_database(self.db)

        # ── shared state ────────────────────────────
        self.current_user = None   # dict set after login
        self.frames = {}           # name → Frame cache
        self.messages_target = None  # optional pre-selected contact for MessagesView

        # ── background reminder / email scheduler ───
        self.reminder_scheduler = ReminderScheduler(self.db, poll_seconds=30)
        self.reminder_scheduler.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── container for all pages ─────────────────
        self.container = tk.Frame(self, bg="#0D1F2D")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # ── show login first ─────────────────────────
        self.show_login()

    def _on_close(self):
        self.reminder_scheduler.stop()
        self.destroy()

    # ── navigation helpers ───────────────────────────
    def show_login(self):
        self._clear_container()
        from views.login import LoginView
        view = LoginView(self.container, self)
        view.pack(fill="both", expand=True)

    def show_register(self):
        self._clear_container()
        from views.register import RegisterView
        view = RegisterView(self.container, self)
        view.pack(fill="both", expand=True)

    def show_client_dashboard(self):
        self._clear_container()
        from views.client_dashboard import ClientDashboard
        view = ClientDashboard(self.container, self)
        view.pack(fill="both", expand=True)

    def show_therapist_dashboard(self):
        self._clear_container()
        from views.therapist_dashboard import TherapistDashboard
        view = TherapistDashboard(self.container, self)
        view.pack(fill="both", expand=True)

    def show_admin_dashboard(self):
        self._clear_container()
        from views.admin_dashboard import AdminDashboard
        view = AdminDashboard(self.container, self)
        view.pack(fill="both", expand=True)

    def show_find_therapist(self):
        self._clear_container()
        from views.find_therapist import FindTherapistView
        view = FindTherapistView(self.container, self)
        view.pack(fill="both", expand=True)

    def show_therapist_profile(self, therapist_id):
        self._clear_container()
        from views.therapist_profile import TherapistProfileView
        view = TherapistProfileView(self.container, self, therapist_id)
        view.pack(fill="both", expand=True)

    def show_book_appointment(self, therapist_id):
        self._clear_container()
        from views.book_appointment import BookAppointmentView
        view = BookAppointmentView(self.container, self, therapist_id)
        view.pack(fill="both", expand=True)

    def show_payment(self, booking_details):
        """booking_details: dict with client_id, therapist_id, date, time, type, notes, amount"""
        self._clear_container()
        from views.payment import PaymentView
        view = PaymentView(self.container, self, booking_details)
        view.pack(fill="both", expand=True)

    def show_messages(self):
        self._clear_container()
        from views.messages import MessagesView
        view = MessagesView(self.container, self)
        view.pack(fill="both", expand=True)

    def logout(self):
        self.current_user = None
        self.show_login()

    def _clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def navigate_after_login(self):
        role = self.current_user.get("role")
        if role == "client":
            self.show_client_dashboard()
        elif role == "therapist":
            self.show_therapist_dashboard()
        elif role == "admin":
            self.show_admin_dashboard()


if __name__ == "__main__":
    app = App()
    app.mainloop()
