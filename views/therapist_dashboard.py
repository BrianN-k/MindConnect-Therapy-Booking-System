"""Therapist dashboard — overview, schedule, clients, availability, profile."""

import tkinter as tk
from tkinter import ttk, messagebox
from views.styles import (C, FS, label, button, card_frame,
                          status_badge, sidebar_btn)
from views import charts
from datetime import datetime


DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
TIMES = ["08:00","09:00","10:00","11:00","12:00","13:00",
         "14:00","15:00","16:00","17:00","18:00"]


def _fmt_date(d):
    try: return datetime.strptime(d, "%Y-%m-%d").strftime("%a %d %b %Y")
    except: return d or "—"

def _fmt_time(t):
    if not t: return "—"
    try:
        h, m = t.split(":"); h = int(h)
        return f"{h if h<=12 else h-12}:{m} {'AM' if h<12 else 'PM'}"
    except: return t


class TherapistDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_dark"])
        self.app  = app
        self.user = app.current_user
        self.therapist = app.db.get_therapist_by_user(self.user["id"])
        if not self.therapist:
            # create a bare profile if a therapist user has none (edge case)
            tid = app.db.create_therapist_profile(self.user["id"], title="Therapist")
            self.therapist = app.db.get_therapist_by_id(tid)
        self._build()
        self._show_section("overview")

    # ════════════════════════════════════════════════
    def _build(self):
        nav = tk.Frame(self, bg=C["teal_900"], height=56)
        nav.pack(fill="x"); nav.pack_propagate(False)
        inner = tk.Frame(nav, bg=C["teal_900"]); inner.pack(fill="both", expand=True, padx=20)
        label(inner, "⊕  MindConnect", size="h3", bold=True, color=C["teal_300"],
              bg=C["teal_900"]).pack(side="left", pady=14)
        label(inner, self.user["name"], size="small", color=C["teal_200"],
              bg=C["teal_900"]).pack(side="right", pady=14, padx=8)
        button(inner, "Sign out", self.app.logout, style="ghost").pack(side="right", pady=10)

        body = tk.Frame(self, bg=C["bg_dark"]); body.pack(fill="both", expand=True)

        self._sidebar = tk.Frame(body, bg=C["teal_900"], width=220)
        self._sidebar.pack(side="left", fill="y"); self._sidebar.pack_propagate(False)
        self._build_sidebar()

        self._main = tk.Frame(body, bg=C["bg_mid"]); self._main.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        badge = tk.Frame(self._sidebar, bg=C["teal_900"]); badge.pack(fill="x", padx=16, pady=20)
        initials = "".join(w[0] for w in self.user["name"].split()[:2]).upper()
        tk.Label(badge, text=initials, width=4, height=2,
                 bg=C["teal_700"], fg=C["text_primary"],
                 font=("Helvetica", FS["h4"], "bold")).pack(side="left", padx=(0, 10))
        col = tk.Frame(badge, bg=C["teal_900"]); col.pack(side="left")
        label(col, self.user["name"], size="body", bold=True, bg=C["teal_900"]).pack(anchor="w")
        label(col, "Therapist", size="small", color=C["teal_300"], bg=C["teal_900"]).pack(anchor="w")

        tk.Frame(self._sidebar, bg=C["teal_700"], height=1).pack(fill="x", pady=(0, 8))

        nav = [("overview",     "🏠", "Overview"),
               ("schedule",     "📅", "Schedule"),
               ("clients",      "👥", "Clients"),
               ("earnings",     "💰", "Earnings"),
               ("messages",     "💬", "Messages"),
               ("availability", "🕐", "Availability"),
               ("profile",      "👤", "My Profile")]
        for key, icon, txt in nav:
            sidebar_btn(self._sidebar, txt, icon, lambda k=key: self._show_section(k))

    def _show_section(self, name):
        for w in self._main.winfo_children(): w.destroy()
        getattr(self, f"_section_{name}")()

    # ════════════════════════════════════════════════
    # OVERVIEW
    # ════════════════════════════════════════════════
    def _section_overview(self):
        p = self._page("Overview", f"Welcome back, {self.user['name'].split()[-1]} 👋")
        apts = self.app.db.get_appointments_for_therapist(self.therapist["id"])
        completed_revenue = sum(a["amount"] for a in apts if a["status"] == "completed")

        stats_row = tk.Frame(p, bg=C["bg_mid"]); stats_row.pack(fill="x", pady=(0, 20))
        for num, lbl, col in [
            (len(apts), "Total appointments", C["teal_500"]),
            (sum(1 for a in apts if a["status"] in ("confirmed","pending")), "Upcoming", C["sage_400"]),
            (len({a["client_id"] for a in apts}), "Active clients", C["amber_400"]),
            (f"KSh {completed_revenue:,}", "Revenue", C["teal_300"]),
        ]:
            c = card_frame(stats_row); c.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h2" if isinstance(num,str) else "h1", bold=True,
                  bg=C["bg_card"]).pack(padx=16, pady=(8, 0))
            label(c, lbl, size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(padx=16, pady=(0, 14))

        # Upcoming sessions
        upcoming = [a for a in apts if a["status"] == "confirmed"][:4]
        up_card = card_frame(p); up_card.pack(fill="x", pady=(0, 16))
        label(up_card, "Upcoming sessions", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))
        if upcoming:
            for a in upcoming: self._client_apt_row(up_card, a)
        else:
            label(up_card, "No upcoming confirmed sessions.", size="body",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=16)

        # Pending requests
        pending = [a for a in apts if a["status"] == "pending"]
        pend_card = card_frame(p); pend_card.pack(fill="x")
        hdr = tk.Frame(pend_card, bg=C["bg_card"]); hdr.pack(fill="x", padx=16, pady=(12, 8))
        label(hdr, "Pending requests", size="h4", bold=True, bg=C["bg_card"]).pack(side="left")
        if pending:
            tk.Label(hdr, text=f" {len(pending)} pending ", bg=C["amber_100"],
                     fg=C["amber_600"], font=("Helvetica", FS["small"], "bold")).pack(side="right")
        if pending:
            for a in pending: self._client_apt_row(pend_card, a, pending=True)
        else:
            label(pend_card, "No pending requests.", size="body",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=16)

    def _client_apt_row(self, parent, a, pending=False):
        client = self.app.db.get_user_by_id(a["client_id"])
        row = tk.Frame(parent, bg=C["bg_card"]); row.pack(fill="x")
        tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
        inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x", padx=16, pady=10)

        initials = "".join(w[0] for w in (client["name"] if client else "??").split()[:2]).upper()
        tk.Label(inner, text=initials, width=4, height=2,
                 bg=C["teal_700"] if not pending else C["amber_400"],
                 fg=C["text_primary"], font=("Helvetica", FS["small"], "bold")).pack(side="left", padx=(0, 10))
        col = tk.Frame(inner, bg=C["bg_card"]); col.pack(side="left", expand=True, fill="x")
        label(col, client["name"] if client else "Client", size="body", bold=True,
              bg=C["bg_card"]).pack(anchor="w")
        label(col, f"{_fmt_date(a['date'])} at {_fmt_time(a['time'])} · {a['type']}",
              size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w")

        if pending:
            button(inner, "Accept", lambda aid=a["id"]: self._update_status(aid, "confirmed"),
                   style="success").pack(side="right", padx=(6,0), ipady=2)
            button(inner, "Decline", lambda aid=a["id"]: self._update_status(aid, "cancelled"),
                   style="danger").pack(side="right", ipady=2)
        else:
            status_badge(inner, a["status"]).pack(side="right")

    def _update_status(self, aid, status):
        waiter = self.app.db.update_appointment_status(aid, status)
        if waiter:
            from services import email_service
            subj, body = email_service.compose_waitlist_opening(
                waiter["client_name"], waiter["therapist_name"])
            email_service.send_async(self.app.db, waiter["client_email"], subj, body)
        messagebox.showinfo("Updated", f"Appointment marked as {status}." +
            (" A waitlisted client has been notified." if waiter else ""))
        self._show_section("overview")

    # ════════════════════════════════════════════════
    # SCHEDULE
    # ════════════════════════════════════════════════
    def _section_schedule(self):
        p = self._page("Schedule", "All your appointments")
        apts = self.app.db.get_appointments_for_therapist(self.therapist["id"])

        nb = ttk.Notebook(p); nb.pack(fill="both", expand=True, pady=(16, 0))
        for tab_name, statuses in [
            ("Upcoming", ["confirmed","pending"]),
            ("Completed", ["completed"]),
            ("Cancelled", ["cancelled"]),
        ]:
            tab = tk.Frame(nb, bg=C["bg_mid"]); nb.add(tab, text=f"  {tab_name}  ")
            subset = [a for a in apts if a["status"] in statuses]
            if subset:
                c = card_frame(tab); c.pack(fill="x", pady=12)
                for a in subset: self._client_apt_row(c, a, pending=(a["status"]=="pending"))
            else:
                label(tab, "No appointments in this category.", size="body",
                      color=C["text_secondary"], bg=C["bg_mid"]).pack(pady=32)

    # ════════════════════════════════════════════════
    # CLIENTS
    # ════════════════════════════════════════════════
    def _section_clients(self):
        p = self._page("My Clients", "Everyone you've worked with")
        apts = self.app.db.get_appointments_for_therapist(self.therapist["id"])
        client_ids = {}
        for a in apts:
            client_ids.setdefault(a["client_id"], []).append(a)

        if not client_ids:
            label(p, "No clients yet.", size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Client",26),("Sessions",10),("Last session",18),("Next session",18),("",14)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for cid, alist in client_ids.items():
            client = self.app.db.get_user_by_id(cid)
            last = sorted([a for a in alist if a["status"]=="completed"], key=lambda a:a["date"], reverse=True)
            nxt  = sorted([a for a in alist if a["status"] in ("confirmed","pending")], key=lambda a:a["date"])

            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, client["name"] if client else "—", size="body", bold=True,
                  bg=C["bg_card"], width=26, anchor="w").pack(side="left", padx=12, pady=10)
            label(inner, str(len(alist)), size="body", color=C["text_secondary"],
                  bg=C["bg_card"], width=10, anchor="w").pack(side="left")
            label(inner, _fmt_date(last[0]["date"]) if last else "—", size="body",
                  color=C["text_secondary"], bg=C["bg_card"], width=18, anchor="w").pack(side="left")
            label(inner, _fmt_date(nxt[0]["date"]) if nxt else "—", size="body",
                  color=C["text_secondary"], bg=C["bg_card"], width=18, anchor="w").pack(side="left")
            button(inner, "Message", lambda cid_=cid: self._go_message(cid_),
                   style="ghost").pack(side="right", padx=12, pady=6, ipady=2)

    def _go_message(self, client_id):
        self.app.messages_target = client_id
        self.app.show_messages()

    # ════════════════════════════════════════════════
    # EARNINGS
    # ════════════════════════════════════════════════
    def _section_earnings(self):
        p = self._page("Earnings", "Revenue and payment history")
        payments = self.app.db.get_payments_for_therapist(self.therapist["id"])

        total_earned = sum(pm["amount"] for pm in payments if pm["status"] == "completed")
        pending_amt  = sum(pm["amount"] for pm in payments if pm["status"] == "pending")
        this_month_total = sum(
            pm["amount"] for pm in payments
            if pm["status"] == "completed" and pm["paid_at"][:7] == datetime.now().strftime("%Y-%m")
        )

        stats_row = tk.Frame(p, bg=C["bg_mid"]); stats_row.pack(fill="x", pady=(0, 20))
        for num, lbl, col in [
            (f"KSh {total_earned:,}",     "Total earned",          C["teal_500"]),
            (f"KSh {this_month_total:,}", "This month",            C["sage_400"]),
            (f"KSh {pending_amt:,}",      "Pending / insurance",   C["amber_400"]),
            (len(payments),               "Total transactions",    C["teal_300"]),
        ]:
            c = card_frame(stats_row); c.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h2", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8, 0))
            label(c, lbl, size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(padx=16, pady=(0, 14))

        # ── revenue over time chart ──────────────────
        chart_card = card_frame(p); chart_card.pack(fill="x", pady=(0, 16))
        label(chart_card, "Revenue by month", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 4))
        rev_data = self.app.db.get_revenue_by_month(self.therapist["id"])
        chart_holder = tk.Frame(chart_card, bg=C["bg_card"]); chart_holder.pack(fill="x", padx=16, pady=(0, 16))
        if rev_data:
            months  = [m for m, _ in rev_data]
            amounts = [a for _, a in rev_data]
            widget = charts.line_chart(chart_holder, months, amounts,
                                       title="", ylabel="KSh", color=C["teal_400"])
            widget.pack(fill="x")
        else:
            label(chart_holder, "No completed payments yet — chart will appear once you have earnings.",
                  size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(pady=20)

        # ── payment status breakdown pie ─────────────
        pie_card = card_frame(p); pie_card.pack(fill="x", pady=(0, 16))
        label(pie_card, "Payments by method", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 4))
        pie_holder = tk.Frame(pie_card, bg=C["bg_card"]); pie_holder.pack(fill="x", padx=16, pady=(0, 16))
        method_counts = {}
        for pm in payments:
            method_counts[pm["method"]] = method_counts.get(pm["method"], 0) + 1
        if method_counts:
            widget = charts.pie_chart(pie_holder, list(method_counts.keys()),
                                      list(method_counts.values()), title="")
            widget.pack()
        else:
            label(pie_holder, "No payments recorded yet.", size="small",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(pady=20)

        # ── transaction table ────────────────────────
        table_card = card_frame(p); table_card.pack(fill="x")
        label(table_card, "Transaction history", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 8))
        if not payments:
            label(table_card, "No transactions yet.", size="body",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=(0, 16))
        else:
            hdr = tk.Frame(table_card, bg=C["bg_dark"]); hdr.pack(fill="x")
            for col, w in [("Client",22),("Session",16),("Method",12),("Reference",14),("Status",12),("Amount",10)]:
                label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                      bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)
            for pm in payments:
                row = tk.Frame(table_card, bg=C["bg_card"]); row.pack(fill="x")
                tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
                inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
                label(inner, pm.get("client_name",""), size="small", bold=True,
                      bg=C["bg_card"], width=22, anchor="w").pack(side="left", padx=12, pady=8)
                label(inner, _fmt_date(pm.get("appt_date","")), size="small",
                      color=C["text_secondary"], bg=C["bg_card"], width=16, anchor="w").pack(side="left")
                label(inner, pm.get("method","").upper(), size="small",
                      color=C["text_secondary"], bg=C["bg_card"], width=12, anchor="w").pack(side="left")
                label(inner, pm.get("transaction_ref","—"), size="small",
                      color=C["text_secondary"], bg=C["bg_card"], width=14, anchor="w").pack(side="left")
                status_badge(inner, pm.get("status","")).pack(side="left", padx=8)
                label(inner, f"KSh {pm.get('amount',0):,}", size="small", bold=True,
                      bg=C["bg_card"], width=10, anchor="w").pack(side="left")
            tk.Frame(table_card, bg=C["bg_card"], height=8).pack()

    # ════════════════════════════════════════════════
    # MESSAGES
    # ════════════════════════════════════════════════
    def _section_messages(self):
        self.app.show_messages()

    # ════════════════════════════════════════════════
    # AVAILABILITY
    # ════════════════════════════════════════════════
    def _section_availability(self):
        p = self._page("Manage Availability", "Set your weekly schedule")
        button(p, "Save availability", self._save_availability,
               style="primary").place(relx=1, rely=0, anchor="ne")

        current = self.app.db.get_availability(self.therapist["id"])
        self._avail_vars = {}   # day -> {time: BooleanVar}
        self._day_enabled = {}  # day -> BooleanVar

        for day in DAYS:
            c = card_frame(p); c.pack(fill="x", pady=(0, 12))
            hdr = tk.Frame(c, bg=C["bg_card"]); hdr.pack(fill="x", padx=16, pady=(10, 4))
            enabled_var = tk.BooleanVar(value=day in current)
            self._day_enabled[day] = enabled_var
            cb = tk.Checkbutton(hdr, text=f"  {day}", variable=enabled_var,
                bg=C["bg_card"], fg=C["text_primary"], selectcolor=C["teal_700"],
                activebackground=C["bg_card"], font=("Helvetica", FS["body"], "bold"),
                command=lambda d=day: self._toggle_day(d))
            cb.pack(side="left")

            slot_frame = tk.Frame(c, bg=C["bg_card"])
            slot_frame.pack(fill="x", padx=16, pady=(0, 12))
            self._avail_vars[day] = {}
            row = None
            for i, t in enumerate(TIMES):
                if i % 6 == 0:
                    row = tk.Frame(slot_frame, bg=C["bg_card"]); row.pack(fill="x", pady=2)
                v = tk.BooleanVar(value=t in current.get(day, []))
                self._avail_vars[day][t] = v
                cb2 = tk.Checkbutton(row, text=_fmt_time(t), variable=v,
                    bg=C["bg_card"], fg=C["text_secondary"], selectcolor=C["teal_700"],
                    activebackground=C["bg_card"], font=("Helvetica", FS["small"]))
                cb2.pack(side="left", padx=(0, 10))
            setattr(self, f"_slotframe_{day}", slot_frame)
            if not enabled_var.get():
                slot_frame.pack_forget()

    def _toggle_day(self, day):
        frame = getattr(self, f"_slotframe_{day}")
        if self._day_enabled[day].get():
            frame.pack(fill="x", padx=16, pady=(0, 12))
        else:
            frame.pack_forget()

    def _save_availability(self):
        for day in DAYS:
            if self._day_enabled[day].get():
                slots = [t for t, v in self._avail_vars[day].items() if v.get()]
                self.app.db.set_availability(self.therapist["id"], day, slots)
            else:
                self.app.db.set_availability(self.therapist["id"], day, [])
        messagebox.showinfo("Saved", "Your availability has been updated.")

    # ════════════════════════════════════════════════
    # PROFILE
    # ════════════════════════════════════════════════
    def _section_profile(self):
        p = self._page("Therapist Profile", "How clients see you")
        c = card_frame(p); c.pack(fill="x", pady=(0, 16))
        label(c, "Professional information", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))

        fields = tk.Frame(c, bg=C["bg_card"]); fields.pack(fill="x", padx=16)

        t = self.therapist
        self._title_var = tk.StringVar(value=t.get("title",""))
        self._price_var = tk.StringVar(value=str(t.get("price",0)))
        self._loc_var   = tk.StringVar(value=t.get("location",""))
        self._specs_var = tk.StringVar(value=t.get("specialities",""))
        self._ins_var   = tk.StringVar(value=t.get("insurance",""))
        self._about_txt = None

        row1 = tk.Frame(fields, bg=C["bg_card"]); row1.pack(fill="x", pady=(8,0))
        for lbl_txt, var, w in [("Professional title", self._title_var, 30),
                                  ("Session price (KSh)", self._price_var, 14)]:
            col = tk.Frame(row1, bg=C["bg_card"]); col.pack(side="left", padx=(0,20))
            label(col, lbl_txt, size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w")
            ttk.Entry(col, textvariable=var, width=w).pack(ipady=4, pady=(2,0))

        label(fields, "Location", size="label", color=C["text_secondary"],
              bg=C["bg_card"]).pack(anchor="w", pady=(12,2))
        ttk.Entry(fields, textvariable=self._loc_var, width=48).pack(anchor="w", ipady=4)

        label(fields, "About / Bio", size="label", color=C["text_secondary"],
              bg=C["bg_card"]).pack(anchor="w", pady=(12,2))
        self._about_txt = tk.Text(fields, height=4, width=60, bg=C["bg_dark"],
            fg=C["text_primary"], insertbackground=C["teal_400"],
            font=("Helvetica", FS["body"]), relief="flat", wrap="word")
        self._about_txt.pack(anchor="w", ipady=4)
        self._about_txt.insert("1.0", t.get("about",""))

        label(fields, "Specialities (comma-separated)", size="label",
              color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(12,2))
        ttk.Entry(fields, textvariable=self._specs_var, width=60).pack(anchor="w", ipady=4)

        label(fields, "Insurance accepted (comma-separated)", size="label",
              color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(12,2))
        ttk.Entry(fields, textvariable=self._ins_var, width=60).pack(anchor="w", ipady=4)

        chk_row = tk.Frame(fields, bg=C["bg_card"]); chk_row.pack(anchor="w", pady=(12,0))
        self._free_var = tk.BooleanVar(value=bool(t.get("free_available")))
        self._online_var = tk.BooleanVar(value=bool(t.get("online")))
        self._inperson_var = tk.BooleanVar(value=bool(t.get("in_person")))
        for txt, var in [("Offer free sessions", self._free_var),
                         ("Available online", self._online_var),
                         ("Available in-person", self._inperson_var)]:
            tk.Checkbutton(chk_row, text=txt, variable=var,
                bg=C["bg_card"], fg=C["text_primary"], selectcolor=C["teal_700"],
                activebackground=C["bg_card"], font=("Helvetica", FS["small"])).pack(side="left", padx=(0,16))

        self._psave_lbl = label(c, "", size="small", color=C["green_400"], bg=C["bg_card"])
        self._psave_lbl.pack(anchor="w", padx=16, pady=(12,0))
        button(c, "Save profile", self._save_profile, style="primary").pack(
            anchor="w", padx=16, pady=(8, 16), ipady=4)

    def _save_profile(self):
        try: price = int(self._price_var.get())
        except ValueError: price = 0
        self.app.db.update_therapist(
            self.therapist["id"],
            title=self._title_var.get(),
            price=price,
            location=self._loc_var.get(),
            specialities=self._specs_var.get(),
            insurance=self._ins_var.get(),
            about=self._about_txt.get("1.0","end").strip(),
            free_available=1 if self._free_var.get() else 0,
            online=1 if self._online_var.get() else 0,
            in_person=1 if self._inperson_var.get() else 0,
        )
        self.therapist = self.app.db.get_therapist_by_id(self.therapist["id"])
        self._psave_lbl.config(text="✓ Profile updated successfully.")
        self.after(3000, lambda: self._psave_lbl.config(text=""))

    # ════════════════════════════════════════════════
    def _page(self, title, subtitle=""):
        f = tk.Frame(self._main, bg=C["bg_mid"]); f.pack(fill="both", expand=True)
        hdr = tk.Frame(f, bg=C["bg_mid"]); hdr.pack(fill="x", padx=28, pady=(24, 16))
        label(hdr, title, size="h2", bold=True, bg=C["bg_mid"]).pack(anchor="w")
        if subtitle:
            label(hdr, subtitle, size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(anchor="w", pady=(2,0))

        canvas = tk.Canvas(f, bg=C["bg_mid"], highlightthickness=0)
        vsb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); canvas.pack(fill="both", expand=True)
        content = tk.Frame(canvas, bg=C["bg_mid"])
        win = canvas.create_window((0,0), window=content, anchor="nw")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        inner = tk.Frame(content, bg=C["bg_mid"])
        inner.pack(fill="both", expand=True, padx=28, pady=(0, 32))
        return inner
