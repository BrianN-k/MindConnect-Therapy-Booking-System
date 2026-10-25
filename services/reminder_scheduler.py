"""
Background thread that polls the `reminders` table and sends any that
are due. Started once from main.py and runs for the lifetime of the app.

Because it never touches Tkinter widgets — only the database and the
network — it's safe to run on a daemon thread alongside the Tkinter
mainloop.
"""

import threading
from services import email_service


class ReminderScheduler:
    def __init__(self, db, poll_seconds=30):
        self.db = db
        self.poll_seconds = poll_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self._process_due()
            except Exception as e:
                print(f"[ReminderScheduler] error: {e}")
            self._stop_event.wait(self.poll_seconds)

    def _process_due(self):
        due = self.db.get_due_reminders()
        for r in due:
            hours_before = 24 if r["type"] == "email" else 1
            subject, body = email_service.compose_reminder(
                client_name=r["client_name"],
                therapist_name=r["therapist_name"],
                date_=r["appt_date"],
                time_=r["appt_time"],
                hours_before=hours_before,
            )
            email_service.send_now(
                self.db, r["client_email"], subject, body,
                related_appointment=r["appointment_id"]
            )
            self.db.mark_reminder_sent(r["id"])
