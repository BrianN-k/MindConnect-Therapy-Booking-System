"""Admin dashboard — system-wide oversight of users, appointments, and analytics."""

import tkinter as tk
from tkinter import ttk, messagebox
from views.styles import C, FS, label, button, card_frame, status_badge, sidebar_btn, entry
from views import charts
from datetime import datetime


def _fmt_date(d):
    try: return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
    except: return d or "—"


class AdminDashboard(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_dark"])
        self.app = app
        self.user = app.current_user
        self._build()
        self._show_section("overview")

    def _build(self):
        nav = tk.Frame(self, bg=C["slate_900"], height=56)
        nav.pack(fill="x"); nav.pack_propagate(False)
        inner = tk.Frame(nav, bg=C["slate_900"]); inner.pack(fill="both", expand=True, padx=20)
        label(inner, "⊕  MindConnect", size="h3", bold=True, color=C["amber_400"],
              bg=C["slate_900"]).pack(side="left", pady=14)
        label(inner, "ADMIN", bg=C["amber_400"], fg=C["slate_900"],
              font=("Helvetica", FS["small"], "bold")).pack(side="left", padx=12, ipadx=8, ipady=2)
        label(inner, self.user["name"], size="small", color=C["text_secondary"],
              bg=C["slate_900"]).pack(side="right", pady=14, padx=8)
        button(inner, "Sign out", self.app.logout, style="ghost").pack(side="right", pady=10)

        body = tk.Frame(self, bg=C["bg_dark"]); body.pack(fill="both", expand=True)
        self._sidebar = tk.Frame(body, bg=C["bg_dark"], width=220)
        self._sidebar.pack(side="left", fill="y"); self._sidebar.pack_propagate(False)
        self._build_sidebar()
        self._main = tk.Frame(body, bg=C["bg_mid"]); self._main.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        badge = tk.Frame(self._sidebar, bg=C["bg_dark"]); badge.pack(fill="x", padx=16, pady=20)
        tk.Label(badge, text="⚙", width=4, height=2, bg=C["amber_400"],
                 fg=C["slate_900"], font=("Helvetica", FS["h4"], "bold")).pack(side="left", padx=(0,10))
        col = tk.Frame(badge, bg=C["bg_dark"]); col.pack(side="left")
        label(col, self.user["name"], size="body", bold=True, bg=C["bg_dark"]).pack(anchor="w")
        label(col, "System Administrator", size="small", color=C["text_secondary"], bg=C["bg_dark"]).pack(anchor="w")

        tk.Frame(self._sidebar, bg=C["bg_card"], height=1).pack(fill="x", pady=(0,8))
        nav = [("overview",     "📊", "Overview"),
               ("appointments", "📅", "All Appointments"),
               ("payments",     "💳", "Payments"),
               ("therapists",   "🩺", "Therapists"),
               ("clients",      "👥", "Clients"),
               ("waitlist",     "⏳", "Waitlist"),
               ("emails",       "📧", "Email Notifications")]
        for key, icon, txt in nav:
            sidebar_btn(self._sidebar, txt, icon, lambda k=key: self._show_section(k))

    def _show_section(self, name):
        for w in self._main.winfo_children(): w.destroy()
        getattr(self, f"_section_{name}")()

    def _reload_section(self, name, *args):
        """Like _show_section but forwards extra args (used by tab switches)."""
        for w in self._main.winfo_children(): w.destroy()
        getattr(self, f"_section_{name}")(*args)

    # ════════════════════════════════════════════════
    # OVERVIEW
    # ════════════════════════════════════════════════
    def _section_overview(self):
        p = self._page("System Overview", "Platform-wide analytics and demand patterns")
        stats = self.app.db.get_stats()

        grid = tk.Frame(p, bg=C["bg_mid"]); grid.pack(fill="x", pady=(0, 20))
        cards = [
            ("Total users",        stats["total_users"],        C["teal_500"]),
            ("Clients",             stats["total_clients"],      C["sage_400"]),
            ("Therapists",          stats["total_therapists"],   C["amber_400"]),
            ("Total appointments",  stats["total_appointments"], C["teal_300"]),
        ]
        row1 = tk.Frame(grid, bg=C["bg_mid"]); row1.pack(fill="x", pady=(0,12))
        for lbl, num, col in cards:
            c = card_frame(row1); c.pack(side="left", fill="x", expand=True, padx=(0,12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h1", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8,0))
            label(c, lbl, size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=(0,14))

        row2 = tk.Frame(grid, bg=C["bg_mid"]); row2.pack(fill="x")
        cards2 = [
            ("Confirmed",  stats["confirmed"], C["green_400"]),
            ("Completed",  stats["completed"], C["slate_400"]),
            ("Cancelled",  stats["cancelled"], C["red_400"]),
            ("Revenue (KSh)", f"{stats['total_revenue']:,}", C["teal_400"]),
        ]
        for lbl, num, col in cards2:
            c = card_frame(row2); c.pack(side="left", fill="x", expand=True, padx=(0,12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h1", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8,0))
            label(c, lbl, size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=(0,14))

        # ── Charts row: demand bar + status pie ──────
        charts_row = tk.Frame(p, bg=C["bg_mid"]); charts_row.pack(fill="x", pady=(8, 16))

        demand_card = card_frame(charts_row); demand_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        label(demand_card, "Appointment demand by therapist", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 4))
        demand_holder = tk.Frame(demand_card, bg=C["bg_card"]); demand_holder.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        therapists = self.app.db.get_all_therapists()
        all_apts = self.app.db.get_all_appointments()
        counts = []
        for t in therapists:
            n = sum(1 for a in all_apts if a["therapist_id"] == t["id"])
            counts.append((t["name"].replace("Dr. ", "").replace("Mr. ", ""), n))
        counts.sort(key=lambda x: -x[1])
        if counts:
            names  = [c[0] for c in counts]
            values = [c[1] for c in counts]
            widget = charts.bar_chart(demand_holder, names, values,
                                      title="", ylabel="Appointments", color=C["teal_400"])
            widget.pack(fill="both", expand=True)
        else:
            label(demand_holder, "No appointment data yet.", size="small",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(pady=20)

        status_card = card_frame(charts_row); status_card.pack(side="left", fill="both", expand=True)
        label(status_card, "Appointment status breakdown", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 4))
        status_holder = tk.Frame(status_card, bg=C["bg_card"]); status_holder.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        status_labels = ["Confirmed", "Completed", "Cancelled"]
        status_values = [stats["confirmed"], stats["completed"], stats["cancelled"]]
        widget = charts.pie_chart(status_holder, status_labels, status_values, title="",
                                  colors=[C["sage_400"], C["slate_400"], C["red_400"]])
        widget.pack()

        # ── Revenue over time ─────────────────────────
        rev_card = card_frame(p); rev_card.pack(fill="x")
        label(rev_card, "Platform revenue by month", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 4))
        rev_holder = tk.Frame(rev_card, bg=C["bg_card"]); rev_holder.pack(fill="x", padx=16, pady=(0, 16))
        rev_data = self.app.db.get_revenue_by_month()
        if rev_data:
            months  = [m for m, _ in rev_data]
            amounts = [a for _, a in rev_data]
            widget = charts.line_chart(rev_holder, months, amounts,
                                       title="", ylabel="KSh", color=C["amber_400"])
            widget.pack(fill="x")
        else:
            label(rev_holder, "No completed payments yet.", size="small",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(pady=20)

    # ════════════════════════════════════════════════
    # ALL APPOINTMENTS
    # ════════════════════════════════════════════════
    def _section_appointments(self):
        p = self._page("All Appointments", "Every booking across the platform")
        apts = self.app.db.get_all_appointments()

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Client",20),("Therapist",20),("Date",14),("Time",10),("Type",10),("Status",12),("Amount",10)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for a in apts:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, a.get("client_name","—"), size="small", bg=C["bg_card"], width=20, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, a.get("therapist_name","—"), size="small", bg=C["bg_card"], width=20, anchor="w").pack(side="left")
            label(inner, _fmt_date(a.get("date","")), size="small", color=C["text_secondary"], bg=C["bg_card"], width=14, anchor="w").pack(side="left")
            label(inner, a.get("time",""), size="small", color=C["text_secondary"], bg=C["bg_card"], width=10, anchor="w").pack(side="left")
            label(inner, a.get("type",""), size="small", color=C["text_secondary"], bg=C["bg_card"], width=10, anchor="w").pack(side="left")
            status_badge(inner, a.get("status","")).pack(side="left", padx=8)
            label(inner, f"KSh {a.get('amount',0):,}", size="small", bg=C["bg_card"], width=10, anchor="w").pack(side="left")

    # ════════════════════════════════════════════════
    # THERAPISTS
    # ════════════════════════════════════════════════
    def _section_therapists(self, tab="active", query=""):
        p = self._page("Therapists", "Manage registered therapists")

        actions = tk.Frame(p, bg=C["bg_mid"]); actions.pack(fill="x", pady=(0, 10))
        button(actions, "+ Add Therapist", self._open_add_therapist_modal,
               style="success").pack(side="left")

        tab_row = tk.Frame(actions, bg=C["bg_mid"]); tab_row.pack(side="right")
        for key, txt in [("active", "Active"), ("archived", "Archived")]:
            active = (key == tab)
            b = button(tab_row, txt, lambda k=key: self._reload_section("therapists", k, self._th_search_var.get()),
                       style="primary" if active else "ghost")
            b.pack(side="left", padx=(8, 0))

        # ── search bar ──
        search_row = tk.Frame(p, bg=C["bg_mid"]); search_row.pack(fill="x", pady=(0, 14))
        if not hasattr(self, "_th_search_var"):
            self._th_search_var = tk.StringVar()
        self._th_search_var.set(query)
        se = ttk.Entry(search_row, textvariable=self._th_search_var, font=("Helvetica", FS["body"]))
        se.pack(side="left", fill="x", expand=True, ipady=5)
        se.bind("<Return>", lambda e: self._reload_section("therapists", tab, self._th_search_var.get()))
        button(search_row, "🔍 Search", lambda: self._reload_section("therapists", tab, self._th_search_var.get()),
               style="primary").pack(side="left", padx=(8, 0), ipady=3)
        if query:
            button(search_row, "Clear", lambda: self._reload_section("therapists", tab, ""),
                   style="ghost").pack(side="left", padx=(8, 0), ipady=3)

        therapists = self.app.db.get_all_therapists(include_archived=True)
        therapists = [t for t in therapists if bool(t.get("is_archived")) == (tab == "archived")]
        if query:
            q = query.lower()
            therapists = [t for t in therapists if q in t.get("name","").lower()
                          or q in t.get("email","").lower()
                          or q in t.get("title","").lower()
                          or q in t.get("location","").lower()]

        if not therapists:
            label(p, f"No {tab} therapists" + (f' matching "{query}"' if query else "") + ".",
                  size="body", color=C["text_secondary"], bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Name",18),("Title",18),("Location",14),("Price",8),("Rating",7),("Status",9),("",20)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for t in therapists:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, t.get("name",""), size="small", bold=True, bg=C["bg_card"], width=18, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, t.get("title",""), size="small", color=C["text_secondary"], bg=C["bg_card"], width=18, anchor="w").pack(side="left")
            label(inner, t.get("location",""), size="small", color=C["text_secondary"], bg=C["bg_card"], width=14, anchor="w").pack(side="left")
            label(inner, f"KSh {t.get('price',0):,}", size="small", bg=C["bg_card"], width=8, anchor="w").pack(side="left")
            label(inner, f"⭐ {t.get('rating',0)}", size="small", color=C["amber_400"], bg=C["bg_card"], width=7, anchor="w").pack(side="left")
            if t.get("is_archived"):
                tk.Label(inner, text=" Archived ", bg=C["slate_100"], fg=C["slate_500"],
                         font=("Helvetica", FS["small"],"bold")).pack(side="left", padx=6)
            else:
                tk.Label(inner, text=" Active ", bg=C["green_100"], fg=C["sage_600"],
                         font=("Helvetica", FS["small"],"bold")).pack(side="left", padx=6)

            btn_box = tk.Frame(inner, bg=C["bg_card"]); btn_box.pack(side="right", padx=12, pady=6)
            button(btn_box, "Edit", lambda th=t: self._open_edit_therapist_modal(th),
                   style="primary").pack(side="left", padx=(0,6), ipady=1)
            if t.get("is_archived"):
                button(btn_box, "Restore", lambda uid=t["user_id"]: self._restore_user(uid, "therapists"),
                       style="success").pack(side="left", padx=(0,6), ipady=1)
            else:
                button(btn_box, "Archive", lambda uid=t["user_id"]: self._archive_user(uid, "therapists"),
                       style="ghost").pack(side="left", padx=(0,6), ipady=1)
                button(btn_box, "Delete", lambda tid=t["id"], nm=t.get("name",""): self._delete_therapist(tid, nm),
                       style="danger").pack(side="left", ipady=1)

    def _archive_user(self, uid, return_section):
        if messagebox.askyesno("Archive account",
            "Archiving hides this account from active lists and prevents them from signing in. "
            "You can restore it at any time. Continue?"):
            self.app.db.archive_user(uid)
            messagebox.showinfo("Archived", "Account archived successfully.")
            self._show_section(return_section)

    def _restore_user(self, uid, return_section):
        self.app.db.unarchive_user(uid)
        messagebox.showinfo("Restored", "Account restored and can sign in again.")
        self._show_section(return_section)

    def _delete_therapist(self, tid, name):
        if not messagebox.askyesno("Delete therapist",
            f"Permanently delete {name}?\n\nThis cannot be undone. If this therapist has "
            "any appointment history, deletion will be blocked — archive them instead."):
            return
        ok, err = self.app.db.delete_therapist(tid)
        if ok:
            messagebox.showinfo("Deleted", f"{name} has been permanently deleted.")
        else:
            messagebox.showwarning("Can't delete", err)
        self._show_section("therapists")

    def _open_add_therapist_modal(self):
        win = tk.Toplevel(self)
        win.title("Add Therapist")
        win.configure(bg=C["bg_card"])
        win.geometry("440x620")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        pad = tk.Frame(win, bg=C["bg_card"]); pad.pack(fill="both", expand=True, padx=24, pady=20)
        label(pad, "Add New Therapist", size="h3", bold=True, bg=C["bg_card"]).pack(anchor="w", pady=(0, 4))
        label(pad, "Creates a login account and a public therapist profile.",
              size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(0, 16))

        fields = {}
        def add_field(key, lbl_text, placeholder="", show=None):
            label(pad, lbl_text, size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(8, 2))
            e, v = entry(pad, placeholder=placeholder, show=show, width=38)
            e.pack(fill="x", ipady=4)
            fields[key] = v

        add_field("name", "Full name*", "Dr. Jane Wanjiru")
        add_field("email", "Email*", "jane.wanjiru@example.com")
        add_field("phone", "Phone", "+254 7XX XXX XXX")
        add_field("password", "Temporary password*", "At least 6 characters", show="•")
        add_field("title", "Professional title", "Clinical Psychologist")
        add_field("speciality", "Specialities (comma-separated)", "Anxiety, Depression, CBT")
        add_field("price", "Session price (KSh)", "2000")
        add_field("location", "Location", "Nairobi")

        err_lbl = label(pad, "", size="small", color=C["red_400"], bg=C["bg_card"])
        err_lbl.pack(anchor="w", pady=(8, 0))

        def submit():
            name = fields["name"].get().strip()
            email = fields["email"].get().strip()
            phone = fields["phone"].get().strip()
            pw = fields["password"].get().strip()
            if not name or name == "Dr. Jane Wanjiru":
                err_lbl.config(text="Full name is required."); return
            if "@" not in email:
                err_lbl.config(text="A valid email is required."); return
            if len(pw) < 6:
                err_lbl.config(text="Password must be at least 6 characters."); return

            uid, dberr = self.app.db.create_user(name, email, pw, "therapist", phone)
            if dberr:
                err_lbl.config(text=dberr); return

            try:
                price = int(fields["price"].get().strip() or 0)
            except ValueError:
                price = 0

            self.app.db.create_therapist_profile(uid,
                title=fields["title"].get().strip(),
                specialities=fields["speciality"].get().strip(),
                price=price,
                location=fields["location"].get().strip(),
            )
            win.destroy()
            messagebox.showinfo("Therapist added", f"{name} has been added and can now sign in.")
            self._show_section("therapists")

        btn_row = tk.Frame(pad, bg=C["bg_card"]); btn_row.pack(fill="x", pady=(16, 0))
        button(btn_row, "Cancel", win.destroy, style="ghost").pack(side="left")
        button(btn_row, "Add Therapist", submit, style="success").pack(side="right")

    def _open_edit_therapist_modal(self, therapist):
        """therapist: dict as returned by get_all_therapists() — includes
        both users-table fields (name/email) and therapists-table fields."""
        win = tk.Toplevel(self)
        win.title("Edit Therapist")
        win.configure(bg=C["bg_card"])
        win.geometry("440x700")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        canvas = tk.Canvas(win, bg=C["bg_card"], highlightthickness=0)
        vsb = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        pad = tk.Frame(canvas, bg=C["bg_card"])
        win_id = canvas.create_window((0, 0), window=pad, anchor="nw")
        pad.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        inner_pad = tk.Frame(pad, bg=C["bg_card"]); inner_pad.pack(fill="both", expand=True, padx=24, pady=20)
        label(inner_pad, f"Edit {therapist.get('name','Therapist')}", size="h3", bold=True,
              bg=C["bg_card"]).pack(anchor="w", pady=(0, 4))
        label(inner_pad, "Changes apply immediately and are visible to clients.",
              size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(0, 16))

        fields = {}
        def add_field(key, lbl_text, default="", show=None):
            label(inner_pad, lbl_text, size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(8, 2))
            e, v = entry(inner_pad, show=show, width=38)
            v.set(default or "")
            e.config(foreground=C["text_primary"])
            e.pack(fill="x", ipady=4)
            fields[key] = v

        add_field("name", "Full name*", therapist.get("name", ""))
        add_field("email", "Email*", therapist.get("email", ""))
        add_field("phone", "Phone", therapist.get("phone", ""))
        add_field("title", "Professional title", therapist.get("title", ""))
        add_field("speciality", "Specialities (comma-separated)", therapist.get("specialities", ""))
        add_field("languages", "Languages (comma-separated)", therapist.get("languages", ""))
        add_field("price", "Session price (KSh)", str(therapist.get("price", 0)))
        add_field("location", "Location", therapist.get("location", ""))
        add_field("insurance", "Insurance accepted (comma-separated)", therapist.get("insurance", ""))

        chk_row = tk.Frame(inner_pad, bg=C["bg_card"]); chk_row.pack(anchor="w", pady=(12, 0))
        free_var = tk.BooleanVar(value=bool(therapist.get("free_available")))
        online_var = tk.BooleanVar(value=bool(therapist.get("online", 1)))
        inperson_var = tk.BooleanVar(value=bool(therapist.get("in_person", 1)))
        for txt, var in [("Free sessions", free_var), ("Online", online_var), ("In-person", inperson_var)]:
            tk.Checkbutton(chk_row, text=txt, variable=var, bg=C["bg_card"], fg=C["text_primary"],
                selectcolor=C["teal_700"], activebackground=C["bg_card"],
                font=("Helvetica", FS["small"])).pack(side="left", padx=(0, 12))

        err_lbl = label(inner_pad, "", size="small", color=C["red_400"], bg=C["bg_card"])
        err_lbl.pack(anchor="w", pady=(10, 0))

        def submit():
            name = fields["name"].get().strip()
            email = fields["email"].get().strip()
            if not name:
                err_lbl.config(text="Full name is required."); return
            if "@" not in email:
                err_lbl.config(text="A valid email is required."); return

            ok, dberr = self.app.db.update_user_admin(
                therapist["user_id"], name, email, fields["phone"].get().strip()
            )
            if not ok:
                err_lbl.config(text=dberr); return

            try:
                price = int(fields["price"].get().strip() or 0)
            except ValueError:
                price = 0

            self.app.db.update_therapist(therapist["id"],
                title=fields["title"].get().strip(),
                specialities=fields["speciality"].get().strip(),
                languages=fields["languages"].get().strip(),
                price=price,
                location=fields["location"].get().strip(),
                insurance=fields["insurance"].get().strip(),
                free_available=1 if free_var.get() else 0,
                online=1 if online_var.get() else 0,
                in_person=1 if inperson_var.get() else 0,
            )
            win.destroy()
            messagebox.showinfo("Saved", f"{name}'s profile has been updated.")
            self._show_section("therapists")

        btn_row = tk.Frame(inner_pad, bg=C["bg_card"]); btn_row.pack(fill="x", pady=(16, 4))
        button(btn_row, "Cancel", win.destroy, style="ghost").pack(side="left")
        button(btn_row, "Save Changes", submit, style="success").pack(side="right")

    # ════════════════════════════════════════════════
    # CLIENTS
    # ════════════════════════════════════════════════
    def _section_clients(self, tab="active", query=""):
        p = self._page("Clients", "All registered clients")

        actions = tk.Frame(p, bg=C["bg_mid"]); actions.pack(fill="x", pady=(0, 10))
        button(actions, "+ Add Client", self._open_add_client_modal,
               style="success").pack(side="left")

        tab_row = tk.Frame(actions, bg=C["bg_mid"]); tab_row.pack(side="right")
        for key, txt in [("active", "Active"), ("archived", "Archived")]:
            active = (key == tab)
            b = button(tab_row, txt, lambda k=key: self._reload_section("clients", k, self._cl_search_var.get()),
                       style="primary" if active else "ghost")
            b.pack(side="left", padx=(8, 0))

        # ── search bar ──
        search_row = tk.Frame(p, bg=C["bg_mid"]); search_row.pack(fill="x", pady=(0, 14))
        if not hasattr(self, "_cl_search_var"):
            self._cl_search_var = tk.StringVar()
        self._cl_search_var.set(query)
        se = ttk.Entry(search_row, textvariable=self._cl_search_var, font=("Helvetica", FS["body"]))
        se.pack(side="left", fill="x", expand=True, ipady=5)
        se.bind("<Return>", lambda e: self._reload_section("clients", tab, self._cl_search_var.get()))
        button(search_row, "🔍 Search", lambda: self._reload_section("clients", tab, self._cl_search_var.get()),
               style="primary").pack(side="left", padx=(8, 0), ipady=3)
        if query:
            button(search_row, "Clear", lambda: self._reload_section("clients", tab, ""),
                   style="ghost").pack(side="left", padx=(8, 0), ipady=3)

        users = self.app.db.get_all_users(role="client", include_archived=True)
        users = [u for u in users if bool(u.get("is_archived")) == (tab == "archived")]
        if query:
            q = query.lower()
            users = [u for u in users if q in u.get("name","").lower()
                    or q in u.get("email","").lower()
                    or q in (u.get("phone") or "").lower()]

        if not users:
            label(p, f"No {tab} clients" + (f' matching "{query}"' if query else "") + ".",
                  size="body", color=C["text_secondary"], bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Name",20),("Email",24),("Phone",15),("Joined",11),("Status",9),("",18)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for u in users:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, u["name"], size="small", bold=True, bg=C["bg_card"], width=20, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, u["email"], size="small", color=C["text_secondary"], bg=C["bg_card"], width=24, anchor="w").pack(side="left")
            label(inner, u.get("phone",""), size="small", color=C["text_secondary"], bg=C["bg_card"], width=15, anchor="w").pack(side="left")
            label(inner, u.get("created_at","")[:10], size="small", color=C["text_secondary"], bg=C["bg_card"], width=11, anchor="w").pack(side="left")
            if u.get("is_archived"):
                tk.Label(inner, text=" Archived ", bg=C["slate_100"], fg=C["slate_500"],
                         font=("Helvetica", FS["small"],"bold")).pack(side="left", padx=6)
            else:
                tk.Label(inner, text=" Active ", bg=C["green_100"], fg=C["sage_600"],
                         font=("Helvetica", FS["small"],"bold")).pack(side="left", padx=6)

            btn_box = tk.Frame(inner, bg=C["bg_card"]); btn_box.pack(side="right", padx=12, pady=6)
            button(btn_box, "Edit", lambda cu=u: self._open_edit_client_modal(cu),
                   style="primary").pack(side="left", padx=(0,6), ipady=1)
            if u.get("is_archived"):
                button(btn_box, "Restore", lambda uid=u["id"]: self._restore_user(uid, "clients"),
                       style="success").pack(side="left", ipady=1)
            else:
                button(btn_box, "Archive", lambda uid=u["id"]: self._archive_user(uid, "clients"),
                       style="ghost").pack(side="left", ipady=1)

    def _open_add_client_modal(self):
        win = tk.Toplevel(self)
        win.title("Add Client")
        win.configure(bg=C["bg_card"])
        win.geometry("420x460")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        pad = tk.Frame(win, bg=C["bg_card"]); pad.pack(fill="both", expand=True, padx=24, pady=20)
        label(pad, "Add New Client", size="h3", bold=True, bg=C["bg_card"]).pack(anchor="w", pady=(0, 4))
        label(pad, "Creates a client account that can sign in immediately.",
              size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(0, 16))

        fields = {}
        def add_field(key, lbl_text, placeholder="", show=None):
            label(pad, lbl_text, size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(8, 2))
            e, v = entry(pad, placeholder=placeholder, show=show, width=38)
            e.pack(fill="x", ipady=4)
            fields[key] = v

        add_field("name", "Full name*", "Amina Odhiambo")
        add_field("email", "Email*", "amina@example.com")
        add_field("phone", "Phone", "+254 7XX XXX XXX")
        add_field("password", "Temporary password*", "At least 6 characters", show="•")

        err_lbl = label(pad, "", size="small", color=C["red_400"], bg=C["bg_card"])
        err_lbl.pack(anchor="w", pady=(8, 0))

        def submit():
            name = fields["name"].get().strip()
            email = fields["email"].get().strip()
            phone = fields["phone"].get().strip()
            pw = fields["password"].get().strip()
            if not name or name == "Amina Odhiambo":
                err_lbl.config(text="Full name is required."); return
            if "@" not in email:
                err_lbl.config(text="A valid email is required."); return
            if len(pw) < 6:
                err_lbl.config(text="Password must be at least 6 characters."); return

            uid, dberr = self.app.db.create_user(name, email, pw, "client", phone)
            if dberr:
                err_lbl.config(text=dberr); return

            win.destroy()
            messagebox.showinfo("Client added", f"{name} has been added and can now sign in.")
            self._show_section("clients")

        btn_row = tk.Frame(pad, bg=C["bg_card"]); btn_row.pack(fill="x", pady=(16, 0))
        button(btn_row, "Cancel", win.destroy, style="ghost").pack(side="left")
        button(btn_row, "Add Client", submit, style="success").pack(side="right")

    def _open_edit_client_modal(self, client_user):
        win = tk.Toplevel(self)
        win.title("Edit Client")
        win.configure(bg=C["bg_card"])
        win.geometry("420x420")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        pad = tk.Frame(win, bg=C["bg_card"]); pad.pack(fill="both", expand=True, padx=24, pady=20)
        label(pad, f"Edit {client_user.get('name','Client')}", size="h3", bold=True,
              bg=C["bg_card"]).pack(anchor="w", pady=(0, 4))
        label(pad, "Changes apply immediately.", size="small",
              color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(0, 16))

        fields = {}
        def add_field(key, lbl_text, default=""):
            label(pad, lbl_text, size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(8, 2))
            e, v = entry(pad, width=38)
            v.set(default or "")
            e.config(foreground=C["text_primary"])
            e.pack(fill="x", ipady=4)
            fields[key] = v

        add_field("name", "Full name*", client_user.get("name", ""))
        add_field("email", "Email*", client_user.get("email", ""))
        add_field("phone", "Phone", client_user.get("phone", ""))

        err_lbl = label(pad, "", size="small", color=C["red_400"], bg=C["bg_card"])
        err_lbl.pack(anchor="w", pady=(8, 0))

        def submit():
            name = fields["name"].get().strip()
            email = fields["email"].get().strip()
            if not name:
                err_lbl.config(text="Full name is required."); return
            if "@" not in email:
                err_lbl.config(text="A valid email is required."); return

            ok, dberr = self.app.db.update_user_admin(
                client_user["id"], name, email, fields["phone"].get().strip()
            )
            if not ok:
                err_lbl.config(text=dberr); return

            win.destroy()
            messagebox.showinfo("Saved", f"{name}'s details have been updated.")
            self._show_section("clients")

        btn_row = tk.Frame(pad, bg=C["bg_card"]); btn_row.pack(fill="x", pady=(16, 0))
        button(btn_row, "Cancel", win.destroy, style="ghost").pack(side="left")
        button(btn_row, "Save Changes", submit, style="success").pack(side="right")

    # ════════════════════════════════════════════════
    # WAITLIST
    # ════════════════════════════════════════════════
    def _section_waitlist(self):
        p = self._page("Waitlist", "Clients waiting for therapist availability")
        rows = self.app.db.conn.execute("""
            SELECT w.*, cu.name as client_name, tu.name as therapist_name
            FROM waitlist w
            JOIN users cu ON cu.id = w.client_id
            JOIN therapists t ON t.id = w.therapist_id
            JOIN users tu ON tu.id = t.user_id
            ORDER BY w.added_at DESC
        """).fetchall()

        if not rows:
            label(p, "No one is currently on a waitlist.", size="body",
                  color=C["text_secondary"], bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Client",22),("Therapist",22),("Added",16),("Status",14)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for r in rows:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, r["client_name"], size="small", bold=True, bg=C["bg_card"], width=22, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, r["therapist_name"], size="small", color=C["text_secondary"], bg=C["bg_card"], width=22, anchor="w").pack(side="left")
            label(inner, _fmt_date(r["added_at"][:10] if r["added_at"] else ""), size="small",
                  color=C["text_secondary"], bg=C["bg_card"], width=16, anchor="w").pack(side="left")
            if r["notified"]:
                tk.Label(inner, text=" Notified ", bg=C["green_100"], fg=C["sage_600"],
                         font=("Helvetica", FS["small"],"bold")).pack(side="left", padx=8)
            else:
                tk.Label(inner, text=" Waiting ", bg=C["teal_100"], fg=C["teal_700"],
                         font=("Helvetica", FS["small"],"bold")).pack(side="left", padx=8)

    # ════════════════════════════════════════════════
    # PAYMENTS
    # ════════════════════════════════════════════════
    def _section_payments(self):
        p = self._page("Payments", "Every transaction processed on the platform")
        payments = self.app.db.get_all_payments()

        total_completed = sum(pm["amount"] for pm in payments if pm["status"] == "completed")
        total_pending   = sum(pm["amount"] for pm in payments if pm["status"] == "pending")
        method_counts = {}
        for pm in payments:
            method_counts[pm["method"]] = method_counts.get(pm["method"], 0) + 1

        stats_row = tk.Frame(p, bg=C["bg_mid"]); stats_row.pack(fill="x", pady=(0, 16))
        for num, lbl, col in [
            (f"KSh {total_completed:,}", "Total collected", C["teal_500"]),
            (f"KSh {total_pending:,}",   "Pending / insurance", C["amber_400"]),
            (len(payments),              "Total transactions", C["sage_400"]),
        ]:
            c = card_frame(stats_row); c.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h2", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8, 0))
            label(c, lbl, size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=(0, 14))

        # Payment method distribution chart
        if method_counts:
            chart_card = card_frame(p); chart_card.pack(fill="x", pady=(0, 16))
            label(chart_card, "Payments by method", size="h4", bold=True,
                  bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 4))
            chart_holder = tk.Frame(chart_card, bg=C["bg_card"]); chart_holder.pack(padx=16, pady=(0, 16))
            widget = charts.pie_chart(chart_holder, list(method_counts.keys()),
                                      list(method_counts.values()), title="")
            widget.pack()

        if not payments:
            label(p, "No payments recorded yet.", size="body",
                  color=C["text_secondary"], bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("Client",18),("Therapist",18),("Session",14),("Method",10),("Reference",14),("Status",12),("Amount",10)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for pm in payments:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, pm.get("client_name",""), size="small", bg=C["bg_card"], width=18, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, pm.get("therapist_name",""), size="small", color=C["text_secondary"], bg=C["bg_card"], width=18, anchor="w").pack(side="left")
            label(inner, _fmt_date(pm.get("appt_date","")), size="small", color=C["text_secondary"], bg=C["bg_card"], width=14, anchor="w").pack(side="left")
            label(inner, pm.get("method","").upper(), size="small", color=C["text_secondary"], bg=C["bg_card"], width=10, anchor="w").pack(side="left")
            label(inner, pm.get("transaction_ref","—"), size="small", color=C["text_secondary"], bg=C["bg_card"], width=14, anchor="w").pack(side="left")
            status_badge(inner, pm.get("status","")).pack(side="left", padx=8)
            label(inner, f"KSh {pm.get('amount',0):,}", size="small", bold=True, bg=C["bg_card"], width=10, anchor="w").pack(side="left")

    # ════════════════════════════════════════════════
    # EMAIL NOTIFICATIONS
    # ════════════════════════════════════════════════
    def _section_emails(self):
        p = self._page("Email Notifications",
                       "Outbox log — booking confirmations, reminders, and receipts")

        from services import email_service
        configured = email_service.is_configured()
        banner = card_frame(p); banner.pack(fill="x", pady=(0, 16))
        if configured:
            label(banner, "✓  SMTP is configured — emails are being sent for real.",
                  size="small", bold=True, color=C["green_400"],
                  bg=C["bg_card"]).pack(anchor="w", padx=16, pady=10)
        else:
            label(banner,
                  "ℹ  Demo mode — no SMTP server configured, so emails are logged "
                  "here instead of being sent. Set MINDCONNECT_SMTP_HOST / "
                  "_USER / _PASSWORD environment variables to send real emails.",
                  size="small", bold=True, color=C["amber_400"],
                  bg=C["bg_card"], wraplength=900, justify="left").pack(anchor="w", padx=16, pady=10)

        outbox = self.app.db.get_email_outbox()

        stats_row = tk.Frame(p, bg=C["bg_mid"]); stats_row.pack(fill="x", pady=(0, 16))
        sent_or_logged = sum(1 for e in outbox if e["status"] in ("sent", "demo_logged"))
        failed = sum(1 for e in outbox if e["status"] == "failed")
        for num, lbl, col in [
            (len(outbox),      "Total emails",  C["teal_500"]),
            (sent_or_logged,   "Sent / logged", C["sage_400"]),
            (failed,           "Failed",        C["red_400"]),
        ]:
            c = card_frame(stats_row); c.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            label(c, str(num), size="h2", bold=True, bg=C["bg_card"]).pack(padx=16, pady=(8, 0))
            label(c, lbl, size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(padx=16, pady=(0, 14))

        if not outbox:
            label(p, "No emails have been queued yet.", size="body",
                  color=C["text_secondary"], bg=C["bg_mid"]).pack(pady=32)
            return

        c = card_frame(p); c.pack(fill="x", pady=12)
        hdr = tk.Frame(c, bg=C["bg_dark"]); hdr.pack(fill="x")
        for col, w in [("To",24),("Subject",38),("Status",14),("Created",18)]:
            label(hdr, col, size="small", bold=True, color=C["text_secondary"],
                  bg=C["bg_dark"], width=w, anchor="w").pack(side="left", padx=(12,0), pady=10)

        for e in outbox[:100]:
            row = tk.Frame(c, bg=C["bg_card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["bg_dark"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["bg_card"]); inner.pack(fill="x")
            label(inner, e.get("to_email",""), size="small", bg=C["bg_card"], width=24, anchor="w").pack(side="left", padx=12, pady=8)
            label(inner, e.get("subject",""), size="small", color=C["text_secondary"],
                  bg=C["bg_card"], width=38, anchor="w").pack(side="left")
            status_map = {"sent": "confirmed", "demo_logged": "waitlisted",
                          "failed": "cancelled", "pending": "pending"}
            status_badge(inner, status_map.get(e.get("status"), "pending")).pack(side="left", padx=8)
            label(inner, e.get("created_at","")[:16], size="small",
                  color=C["text_secondary"], bg=C["bg_card"], width=18, anchor="w").pack(side="left")

    # ════════════════════════════════════════════════
    def _page(self, title, subtitle=""):
        f = tk.Frame(self._main, bg=C["bg_mid"]); f.pack(fill="both", expand=True)
        hdr = tk.Frame(f, bg=C["bg_mid"]); hdr.pack(fill="x", padx=28, pady=(24, 16))
        label(hdr, title, size="h2", bold=True, bg=C["bg_mid"]).pack(anchor="w")
        if subtitle:
            label(hdr, subtitle, size="body", color=C["text_secondary"], bg=C["bg_mid"]).pack(anchor="w", pady=(2,0))

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
