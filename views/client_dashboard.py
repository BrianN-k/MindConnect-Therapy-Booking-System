"""Client dashboard — overview, appointments, waitlist, messages, profile."""

import tkinter as tk
from tkinter import ttk, messagebox
from views.styles import (C, FS, label, button, card_frame,
                          status_badge, sidebar_btn, separator)
from datetime import datetime


def _fmt_date(d):
    try: return datetime.strptime(d, "%Y-%m-%d").strftime("%a %d %b %Y")
    except: return d or "—"

def _fmt_time(t):
    if not t: return "—"
    try:
        h, m = t.split(":")
        h = int(h)
        return f"{h if h<=12 else h-12}:{m} {'AM' if h<12 else 'PM'}"
    except: return t

def _is_future(date_str, time_str):
    """True if the appointment's date/time hasn't happened yet."""
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        return dt > datetime.now()
    except Exception:
        return False


class ClientDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_dark"])
        self.app  = app
        self.user = app.current_user
        self._active_section = None
        self._build()
        self._show_section("overview")

    # ════════════════════════════════════════════════
    # LAYOUT
    # ════════════════════════════════════════════════
    def _build(self):
        # ── top nav ─────────────────────────────────
        nav = tk.Frame(self, bg=C["slate_900"], height=56)
        nav.pack(fill="x"); nav.pack_propagate(False)
        inner = tk.Frame(nav, bg=C["slate_900"]); inner.pack(fill="both", expand=True, padx=20)
        label(inner, "⊕  MindConnect", size="h3", bold=True, color=C["teal_400"],
              bg=C["slate_900"]).pack(side="left", pady=14)
        unread = self.app.db.unread_count(self.user["id"])
        msg_txt = f"💬  Messages" + (f" ({unread})" if unread else "")
        button(inner, msg_txt, lambda: self._show_section("messages"),
               style="ghost").pack(side="right", pady=10, padx=(0, 8))
        label(inner, self.user["name"], size="small", color=C["text_secondary"],
              bg=C["slate_900"]).pack(side="right", pady=14, padx=8)
        button(inner, "Sign out", self.app.logout, style="ghost").pack(
            side="right", pady=10)

        # ── body ────────────────────────────────────
        body = tk.Frame(self, bg=C["bg_dark"]); body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = tk.Frame(body, bg=C["bg_dark"], width=220)
        self._sidebar.pack(side="left", fill="y"); self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Main content
        self._main = tk.Frame(body, bg=C["bg_mid"]); self._main.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        # User badge
        badge = tk.Frame(self._sidebar, bg=C["bg_dark"]); badge.pack(fill="x", padx=16, pady=20)
        initials = "".join(w[0] for w in self.user["name"].split()[:2]).upper()
        av = tk.Label(badge, text=initials, width=4, height=2,
                      bg=C["teal_700"], fg=C["text_primary"],
                      font=("Helvetica", FS["h4"], "bold"))
        av.pack(side="left", padx=(0, 10))
        col = tk.Frame(badge, bg=C["bg_dark"]); col.pack(side="left")
        label(col, self.user["name"], size="body", bold=True, bg=C["bg_dark"]).pack(anchor="w")
        label(col, "Client", size="small", color=C["text_secondary"], bg=C["bg_dark"]).pack(anchor="w")

        tk.Frame(self._sidebar, bg=C["bg_card"], height=1).pack(fill="x", pady=(0, 8))

        self._nav_items = {}
        nav = [("overview",     "🏠", "Overview"),
               ("appointments", "📅", "Appointments"),
               ("find",         "🔍", "Find Therapist"),
               ("payments",     "💳", "Payments"),
               ("messages",     "💬", "Messages"),
               ("waitlist",     "⏳", "Waitlist"),
               ("profile",      "👤", "My Profile")]
        for key, icon, txt in nav:
            b = sidebar_btn(self._sidebar, txt, icon,
                            lambda k=key: self._show_section(k))
            self._nav_items[key] = b

    # ════════════════════════════════════════════════
    # SECTION SWITCHING
    # ════════════════════════════════════════════════
    def _show_section(self, name):
        for w in self._main.winfo_children():
            w.destroy()
        self._active_section = name
        getattr(self, f"_section_{name}")()

    # ════════════════════════════════════════════════
    # OVERVIEW
    # ════════════════════════════════════════════════
    def _section_overview(self):
        p = self._page("Overview", f"Welcome back, {self.user['name'].split()[0]}! 👋")
        button(p, "+ Book a session", self.app.show_find_therapist,
               style="primary").place(relx=1, rely=0, anchor="ne")

        apts = self.app.db.get_appointments_for_client(self.user["id"])

        # Stat cards
        stats_row = tk.Frame(p, bg=C["bg_mid"]); stats_row.pack(fill="x", pady=(0, 20))
        for num, lbl, col in [
            (len(apts),                                  "Total sessions",    C["teal_500"]),
            (sum(1 for a in apts if a["status"] in ("confirmed","pending")), "Upcoming", C["sage_400"]),
            (sum(1 for a in apts if a["status"] == "completed"),             "Completed",C["amber_400"]),
            (len({a["therapist_id"] for a in apts}),                         "Therapists",C["teal_300"]),
        ]:
            c = card_frame(stats_row); c.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h1", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8, 0))
            label(c, lbl, size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(padx=16, pady=(0, 14))

        # Upcoming
        upcoming = [a for a in apts if a["status"] in ("confirmed","pending")][:3]
        up_card = card_frame(p); up_card.pack(fill="x", pady=(0, 16))
        self._card_header(up_card, "Upcoming appointments",
                          action_text="View all", action=lambda: self._show_section("appointments"))
        if upcoming:
            for a in upcoming:
                self._apt_row(up_card, a, show_cancel=True)
        else:
            label(up_card, "No upcoming appointments.",
                  size="body", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(padx=16, pady=20)

        # CTA
        cta = tk.Frame(p, bg=C["teal_900"]); cta.pack(fill="x")
        inner = tk.Frame(cta, bg=C["teal_900"]); inner.pack(fill="x", padx=20, pady=18)
        label(inner, "Ready to book your next session?", size="h3", bold=True,
              bg=C["teal_900"]).pack(side="left")
        button(inner, "Browse therapists →", self.app.show_find_therapist,
               style="primary").pack(side="right", ipady=4)

    # ════════════════════════════════════════════════
    # APPOINTMENTS
    # ════════════════════════════════════════════════
    def _section_appointments(self):
        p = self._page("My Appointments", "Manage all your bookings")
        button(p, "+ Book new", self.app.show_find_therapist,
               style="primary").place(relx=1, rely=0, anchor="ne")

        nb = ttk.Notebook(p); nb.pack(fill="both", expand=True, pady=(16, 0))
        apts = self.app.db.get_appointments_for_client(self.user["id"])

        for tab_name, statuses in [
            ("Upcoming",  ["confirmed","pending"]),
            ("Past",      ["completed"]),
            ("Cancelled", ["cancelled"]),
        ]:
            tab = tk.Frame(nb, bg=C["bg_mid"]); nb.add(tab, text=f"  {tab_name}  ")
            subset = [a for a in apts if a["status"] in statuses]
            self._apt_table(tab, subset, show_cancel=(tab_name == "Upcoming"))

    def _apt_table(self, parent, apts, show_cancel=False):
        if not apts:
            label(parent, "No appointments in this category.",
                  size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(parent); c.pack(fill="x", pady=12, padx=0)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Therapist",30),("Date",20),("Time",12),("Type",12),("Status",14),("",10)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(
                side="left", padx=(12, 0), pady=10)

        for a in apts:
            self._apt_row(c, a, show_cancel=show_cancel)

    def _apt_row(self, parent, a, show_cancel=False):
        row = tk.Frame(parent, bg=C["bg_card"]); row.pack(fill="x")
        tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
        inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")

        label(inner, a.get("therapist_name","—"), size="body", bold=True,
              bg=C["bg_card"], width=28, anchor="w").pack(side="left", padx=12, pady=12)
        label(inner, _fmt_date(a.get("date","")), size="body", color=C["text_secondary"],
              bg=C["bg_card"], width=20, anchor="w").pack(side="left")
        label(inner, _fmt_time(a.get("time","")), size="body", color=C["text_secondary"],
              bg=C["bg_card"], width=12, anchor="w").pack(side="left")
        label(inner, a.get("type","—"), size="body", color=C["text_secondary"],
              bg=C["bg_card"], width=12, anchor="w").pack(side="left")
        status_badge(inner, a.get("status","")).pack(side="left", padx=8)

        if show_cancel and a["status"] in ("confirmed","pending"):
            if _is_future(a.get("date",""), a.get("time","")):
                button(inner, "Reschedule", lambda apt=a: self._open_reschedule_modal(apt),
                       style="primary").pack(side="right", padx=(0,8), pady=8, ipady=2)
            button(inner, "Cancel", lambda aid=a["id"]: self._cancel(aid),
                   style="ghost").pack(side="right", padx=12, pady=8, ipady=2)

    def _cancel(self, aid):
        if messagebox.askyesno("Cancel appointment",
            "Are you sure you want to cancel this appointment?\n"
            "The therapist will be notified. Waitlisted clients will be offered your slot."):
            waiter = self.app.db.update_appointment_status(aid, "cancelled")
            if waiter:
                from services import email_service
                subj, body = email_service.compose_waitlist_opening(
                    waiter["client_name"], waiter["therapist_name"])
                email_service.send_async(self.app.db, waiter["client_email"], subj, body)
            messagebox.showinfo("Cancelled",
                "Appointment cancelled. " +
                ("A waitlisted client has been notified by email." if waiter
                 else "No one was on the waitlist for this slot."))
            self._show_section("appointments")

    def _open_reschedule_modal(self, appointment):
        """Lets the client move an upcoming appointment to a different
        day/time with the same therapist, before the session starts."""
        from views.book_appointment import _next_date_for_day

        therapist = self.app.db.get_therapist_by_id(appointment["therapist_id"])
        if not therapist:
            messagebox.showerror("Error", "Therapist not found.")
            return

        win = tk.Toplevel(self)
        win.title("Reschedule Appointment")
        win.configure(bg=C["bg_card"])
        win.geometry("500x600")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        pad = tk.Frame(win, bg=C["bg_card"]); pad.pack(fill="both", expand=True, padx=24, pady=20)
        label(pad, f"Reschedule with {therapist['name']}", size="h3", bold=True,
              bg=C["bg_card"]).pack(anchor="w")
        label(pad, f"Currently:  {_fmt_date(appointment['date'])}  ·  {_fmt_time(appointment['time'])}",
              size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(2, 18))

        avail = self.app.db.get_availability(appointment["therapist_id"])
        days = list(avail.keys())

        if not days:
            label(pad, "This therapist currently has no availability set. "
                       "Please contact them directly, or try again later.",
                  size="body", color=C["text_secondary"], bg=C["bg_card"],
                  wraplength=420).pack(pady=20)
            button(pad, "Close", win.destroy, style="ghost").pack()
            return

        label(pad, "Select a new day", size="label", color=C["text_secondary"],
              bg=C["bg_card"]).pack(anchor="w", pady=(0, 6))
        day_row = tk.Frame(pad, bg=C["bg_card"]); day_row.pack(fill="x")

        label(pad, "Available times", size="label", color=C["text_secondary"],
              bg=C["bg_card"]).pack(anchor="w", pady=(16, 6))
        slot_frame = tk.Frame(pad, bg=C["bg_card"]); slot_frame.pack(fill="x")

        err_lbl = label(pad, "", size="small", color=C["red_400"], bg=C["bg_card"])
        err_lbl.pack(anchor="w", pady=(12, 4))

        state = {"day": days[0], "date": None, "time": None}

        confirm_btn = button(pad, "Select a new time", None, style="ghost")
        confirm_btn.pack(fill="x", pady=(8, 0), ipady=6)
        confirm_btn.config(state="disabled")

        day_btns = {}

        def render_slots(day):
            state["day"] = day
            state["date"] = None
            state["time"] = None
            confirm_btn.config(state="disabled", text="Select a new time",
                bg=C["bg_card"], fg=C["text_secondary"])
            for d, b in day_btns.items():
                b.config(bg=C["teal_600"] if d == day else C["bg_dark"])
            for w in slot_frame.winfo_children():
                w.destroy()

            slots = avail.get(day, [])
            date_str = _next_date_for_day(day)
            if not slots:
                label(slot_frame, "No slots available this day.", size="small",
                      color=C["text_secondary"], bg=C["bg_card"]).pack(pady=8)
                return

            slot_btns = {}
            row = None
            for i, sl in enumerate(slots):
                if i % 4 == 0:
                    row = tk.Frame(slot_frame, bg=C["bg_card"]); row.pack(fill="x", pady=4)
                is_current = (date_str == appointment["date"] and sl == appointment["time"])
                booked = (not is_current) and self.app.db.is_slot_booked(
                    appointment["therapist_id"], date_str, sl)
                btn = tk.Button(row, text=_fmt_time(sl),
                    state="disabled" if booked else "normal",
                    bg=C["bg_dark"], fg=C["text_secondary"],
                    disabledforeground=C["slate_400"],
                    relief="flat", cursor="hand2" if not booked else "arrow",
                    font=("Helvetica", FS["small"]), padx=10, pady=7)
                btn.config(command=lambda s=sl, d=date_str, b=btn: pick_slot(s, d, b))
                btn.pack(side="left", padx=4)
                slot_btns[sl] = btn

            def pick_slot(slot, date_str, widget):
                state["date"] = date_str
                state["time"] = slot
                for s, b in slot_btns.items():
                    b.config(bg=C["teal_600"] if s == slot else C["bg_dark"],
                             fg=C["text_primary"] if s == slot else C["text_secondary"])
                confirm_btn.config(state="normal", text=f"Confirm new time: {_fmt_time(slot)}",
                    bg=C["teal_600"], fg=C["text_primary"])
                err_lbl.config(text="")

        for day in days:
            b = tk.Button(day_row, text=day[:3], command=lambda d=day: render_slots(d),
                bg=C["teal_600"] if day == days[0] else C["bg_dark"],
                fg=C["text_primary"], relief="flat", cursor="hand2",
                font=("Helvetica", FS["small"]), padx=12, pady=6)
            b.pack(side="left", padx=(0, 6))
            day_btns[day] = b

        def confirm():
            if not state["date"] or not state["time"]:
                err_lbl.config(text="Please select a new time slot."); return
            ok, dberr = self.app.db.reschedule_appointment(
                appointment["id"], state["date"], state["time"])
            if not ok:
                err_lbl.config(text=dberr)
                render_slots(state["day"])  # refresh in case slot was just taken
                return

            from services import email_service
            th_user_email = therapist.get("email", "")
            if th_user_email:
                subj, body = email_service.compose_new_booking_alert_for_therapist(
                    therapist["name"], self.user["name"], state["date"], state["time"],
                    appointment.get("type", "online"))
                subj = "Session rescheduled — " + subj
                email_service.send_async(self.app.db, th_user_email, subj, body)

            win.destroy()
            messagebox.showinfo("Rescheduled",
                f"Your session with {therapist['name']} has been moved to "
                f"{_fmt_date(state['date'])} at {_fmt_time(state['time'])}.")
            self._show_section("appointments")

        confirm_btn.config(command=confirm)
        render_slots(days[0])

    # ════════════════════════════════════════════════
    # FIND
    # ════════════════════════════════════════════════
    def _section_find(self):
        self.app.show_find_therapist()

    # ════════════════════════════════════════════════
    # PAYMENTS
    # ════════════════════════════════════════════════
    def _section_payments(self):
        p = self._page("Payments", "Your payment history and receipts")
        payments = self.app.db.get_payments_for_client(self.user["id"])

        total_paid = sum(pm["amount"] for pm in payments if pm["status"] == "completed")
        pending    = sum(1 for pm in payments if pm["status"] == "pending")

        stats_row = tk.Frame(p, bg=C["bg_mid"]); stats_row.pack(fill="x", pady=(0, 20))
        for num, lbl, col in [
            (f"KSh {total_paid:,}", "Total paid", C["teal_500"]),
            (len(payments),          "Total transactions", C["sage_400"]),
            (pending,                "Pending / insurance", C["amber_400"]),
        ]:
            c = card_frame(stats_row); c.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h2", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8, 0))
            label(c, lbl, size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(padx=16, pady=(0, 14))

        if not payments:
            label(p, "No payments yet.", size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Therapist",22),("Session",16),("Method",12),("Reference",14),("Status",12),("Amount",10)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for pm in payments:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, pm.get("therapist_name",""), size="small", bold=True,
                  bg=C["bg_card"], width=22, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, f"{_fmt_date(pm.get('appt_date',''))}", size="small",
                  color=C["text_secondary"], bg=C["bg_card"], width=16, anchor="w").pack(side="left")
            label(inner, pm.get("method","").upper(), size="small",
                  color=C["text_secondary"], bg=C["bg_card"], width=12, anchor="w").pack(side="left")
            label(inner, pm.get("transaction_ref","—"), size="small",
                  color=C["text_secondary"], bg=C["bg_card"], width=14, anchor="w").pack(side="left")
            status_badge(inner, pm.get("status","")).pack(side="left", padx=8)
            label(inner, f"KSh {pm.get('amount',0):,}", size="small", bold=True,
                  bg=C["bg_card"], width=10, anchor="w").pack(side="left")

    # ════════════════════════════════════════════════
    # MESSAGES
    # ════════════════════════════════════════════════
    def _section_messages(self):
        self.app.show_messages()

    # ════════════════════════════════════════════════
    # WAITLIST
    # ════════════════════════════════════════════════
    def _section_waitlist(self):
        p = self._page("Waitlist", "Therapists you're waiting for")
        entries = self.app.db.get_waitlist_for_client(self.user["id"])
        if not entries:
            label(p, "⏳", size="h1", bg=C["bg_mid"]).pack(pady=(40, 8))
            label(p, "Not on any waitlist.", size="h3", bg=C["bg_mid"]).pack()
            label(p, "Join a waitlist from a therapist's profile when they're fully booked.",
                  size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(pady=(6, 20))
            button(p, "Find a therapist", self.app.show_find_therapist,
                   style="primary").pack(ipady=6)
            return

        for w in entries:
            row = card_frame(p); row.pack(fill="x", pady=(0, 10))
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x", padx=16, pady=14)
            initials = "".join(x[0] for x in w["therapist_name"].split()[:2]).upper()
            av = tk.Label(inner, text=initials, width=4, height=2,
                          bg=C["teal_700"], fg=C["text_primary"],
                          font=("Helvetica", FS["h4"], "bold"))
            av.pack(side="left", padx=(0, 12))
            col = tk.Frame(inner, bg=C["bg_card"]); col.pack(side="left", expand=True)
            label(col, w["therapist_name"], size="body", bold=True, bg=C["bg_card"]).pack(anchor="w")
            label(col, f"Added: {_fmt_date(w.get('added_at',''))}",
                  size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(anchor="w", pady=(2, 0))
            if w.get("notified"):
                label(inner, "🔔  A slot opened!", size="small",
                      color=C["green_400"], bold=True,
                      bg=C["bg_card"]).pack(side="right", padx=12)
                button(inner, "Book now →",
                       lambda tid=w["therapist_id"]: self.app.show_book_appointment(tid),
                       style="primary").pack(side="right", padx=(0, 12), ipady=3)
            else:
                label(inner, "Waiting for slot…", size="small",
                      color=C["teal_300"], bg=C["bg_card"]).pack(side="right", padx=12)
            button(inner, "Remove",
                   lambda wid=w["id"]: self._remove_waitlist(wid),
                   style="ghost").pack(side="right", padx=(0, 8), ipady=3)

    def _remove_waitlist(self, wid):
        self.app.db.remove_from_waitlist(wid)
        self._show_section("waitlist")

    # ════════════════════════════════════════════════
    # PROFILE
    # ════════════════════════════════════════════════
    def _section_profile(self):
        p = self._page("My Profile", "Update your personal information")

        c = card_frame(p); c.pack(fill="x", pady=(0, 16), ipadx=8)
        label(c, "Personal information", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))

        fields = tk.Frame(c, bg=C["bg_card"]); fields.pack(fill="x", padx=16)

        self._pname_var = tk.StringVar(value=self.user.get("name",""))
        self._pemail_var = tk.StringVar(value=self.user.get("email",""))
        self._pphone_var = tk.StringVar(value=self.user.get("phone",""))

        for lbl_txt, var in [("Full name", self._pname_var),
                              ("Email",     self._pemail_var),
                              ("Phone",     self._pphone_var)]:
            label(fields, lbl_txt, size="label", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(anchor="w", pady=(8, 2))
            e = ttk.Entry(fields, textvariable=var, width=40)
            e.pack(anchor="w", ipady=4)

        self._psave_lbl = label(c, "", size="small", color=C["green_400"],
                                bg=C["bg_card"])
        self._psave_lbl.pack(anchor="w", padx=16, pady=(8, 0))
        button(c, "Save changes", self._save_profile,
               style="primary").pack(anchor="w", padx=16, pady=(8, 16), ipady=4)

    def _save_profile(self):
        self.app.db.update_user(
            self.user["id"],
            self._pname_var.get().strip(),
            self._pphone_var.get().strip()
        )
        self.app.current_user["name"] = self._pname_var.get().strip()
        self.user = self.app.current_user
        self._psave_lbl.config(text="✓ Profile saved successfully.")
        self.after(3000, lambda: self._psave_lbl.config(text=""))

    # ════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════
    def _page(self, title, subtitle=""):
        f = tk.Frame(self._main, bg=C["bg_mid"]); f.pack(fill="both", expand=True)

        # Header
        hdr = tk.Frame(f, bg=C["bg_mid"]); hdr.pack(fill="x", padx=28, pady=(24, 16))
        label(hdr, title, size="h2", bold=True, bg=C["bg_mid"]).pack(anchor="w")
        if subtitle:
            label(hdr, subtitle, size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(anchor="w", pady=(2, 0))

        # Scrollable content
        canvas = tk.Canvas(f, bg=C["bg_mid"], highlightthickness=0)
        vsb    = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        content = tk.Frame(canvas, bg=C["bg_mid"])
        win = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        inner = tk.Frame(content, bg=C["bg_mid"])
        inner.pack(fill="both", expand=True, padx=28, pady=(0, 32))
        return inner

    def _card_header(self, parent, title, action_text=None, action=None):
        hdr = tk.Frame(parent, bg=C["bg_card"]); hdr.pack(fill="x", padx=16, pady=(12, 8))
        label(hdr, title, size="h4", bold=True, bg=C["bg_card"]).pack(side="left")
        if action_text and action:
            lk = tk.Label(hdr, text=action_text, bg=C["bg_card"], fg=C["teal_400"],
                font=("Helvetica", FS["small"]), cursor="hand2")
            lk.pack(side="right")
            lk.bind("<Button-1>", lambda e: action())
