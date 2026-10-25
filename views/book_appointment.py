"""Book appointment view — slot picker, session type, notes, confirmation."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from views.styles import C, FS, label, button, card_frame, nav_bar, entry


DAYS_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


def _next_date_for_day(day_name: str) -> str:
    """Return the ISO date string of the next occurrence of day_name."""
    day_idx = DAYS_ORDER.index(day_name)
    today   = datetime.today()
    today_idx = today.weekday()          # Mon=0 … Sun=6
    delta = (day_idx - today_idx) % 7
    if delta == 0:
        delta = 7                        # always use next week if today
    target = today + timedelta(days=delta)
    return target.strftime("%Y-%m-%d")


def _fmt_time(t: str) -> str:
    h, m = t.split(":")
    h = int(h)
    return f"{h if h<=12 else h-12}:{m} {'AM' if h<12 else 'PM'}"


class BookAppointmentView(tk.Frame):
    def __init__(self, parent, app, therapist_id):
        super().__init__(parent, bg=C["bg_mid"])
        self.app  = app
        self.tid  = therapist_id
        self.t    = app.db.get_therapist_by_id(therapist_id)
        self._selected_day  = tk.StringVar()
        self._selected_slot = None      # (date_str, time_str)
        self._session_type  = tk.StringVar(value="online")
        self._build()

    # ════════════════════════════════════════════════
    def _build(self):
        if not self.t:
            label(self, "Therapist not found.").pack(pady=40)
            return

        nav_bar(self, self.app, show_back=True,
                back_cmd=lambda: self.app.show_therapist_profile(self.tid))

        # Page title
        hdr = tk.Frame(self, bg=C["bg_dark"]); hdr.pack(fill="x")
        label(hdr, "Book an appointment", size="h2", bold=True,
              bg=C["bg_dark"]).pack(padx=24, pady=(20, 4))
        label(hdr, f"with {self.t['name']} · {self.t.get('title','')}",
              size="body", color=C["text_secondary"],
              bg=C["bg_dark"]).pack(padx=24, pady=(0, 16))

        # Scrollable body
        canvas = tk.Canvas(self, bg=C["bg_mid"], highlightthickness=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=C["bg_mid"])
        win  = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        cols = tk.Frame(body, bg=C["bg_mid"])
        cols.pack(fill="both", expand=True, padx=24, pady=24)

        left  = tk.Frame(cols, bg=C["bg_mid"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(cols, bg=C["bg_mid"], width=320)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        self._build_summary(right)
        self._build_left(left)

    # ─── LEFT: slot picker ───────────────────────────
    def _build_left(self, parent):
        # Step 1 — choose day
        avail = self.app.db.get_availability(self.tid)
        days  = list(avail.keys())

        step1 = card_frame(parent); step1.pack(fill="x", pady=(0, 16))
        label(step1, "Step 1 — Select a day", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))

        day_row = tk.Frame(step1, bg=C["bg_card"]); day_row.pack(fill="x", padx=16, pady=(0, 14))
        self._day_btns = {}
        if days:
            self._selected_day.set(days[0])
        for day in days:
            next_date = _next_date_for_day(day)
            d_short   = datetime.strptime(next_date, "%Y-%m-%d").strftime("%a %d %b")
            btn = tk.Button(day_row,
                text=f"{day}\n{d_short}",
                command=lambda d=day: self._pick_day(d),
                bg=C["teal_600"] if day == self._selected_day.get() else C["bg_dark"],
                fg=C["text_primary"], relief="flat", cursor="hand2",
                font=("Helvetica", FS["small"]), padx=14, pady=8, justify="center")
            btn.pack(side="left", padx=(0, 8))
            self._day_btns[day] = btn

        # Step 2 — choose slot
        step2 = card_frame(parent); step2.pack(fill="x", pady=(0, 16))
        label(step2, "Step 2 — Choose a time slot", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))
        self._slot_frame = tk.Frame(step2, bg=C["bg_card"])
        self._slot_frame.pack(fill="x", padx=16, pady=(0, 14))

        # Step 3 — session type
        step3 = card_frame(parent); step3.pack(fill="x", pady=(0, 16))
        label(step3, "Step 3 — Session type", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))
        type_row = tk.Frame(step3, bg=C["bg_card"]); type_row.pack(fill="x", padx=16, pady=(0, 12))
        for val, txt, icon in [("online","Online / Video","🖥"),
                                ("in-person","In-person","🏢")]:
            enabled = bool(self.t.get("online") if val == "online" else self.t.get("in_person"))
            if enabled:
                tk.Radiobutton(type_row,
                    text=f"  {icon}  {txt}",
                    variable=self._session_type, value=val,
                    bg=C["bg_card"], fg=C["text_primary"],
                    selectcolor=C["teal_700"],
                    activebackground=C["bg_card"],
                    font=("Helvetica", FS["body"]),
                    command=self._refresh_summary
                ).pack(side="left", padx=(0, 20))

        # Step 4 — notes
        step4 = card_frame(parent); step4.pack(fill="x", pady=(0, 16))
        label(step4, "Step 4 — Notes for therapist (optional)", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))
        self._notes = tk.Text(step4, height=4, bg=C["bg_dark"], fg=C["text_primary"],
            font=("Helvetica", FS["body"]), relief="flat",
            insertbackground=C["teal_400"], wrap="word")
        self._notes.pack(fill="x", padx=16, pady=(0, 14), ipady=4)
        self._notes.insert("1.0", "What brings you here? Anything you'd like them to know…")
        self._notes.config(fg=C["text_secondary"])
        self._notes.bind("<FocusIn>",  self._notes_focus_in)
        self._notes.bind("<FocusOut>", self._notes_focus_out)
        self._notes.bind("<<Modified>>", lambda _: self._refresh_summary())

        if days:
            self._pick_day(days[0])

    def _notes_focus_in(self, _):
        if self._notes.get("1.0", "end").strip() in (
                "", "What brings you here? Anything you'd like them to know…"):
            self._notes.delete("1.0", "end")
            self._notes.config(fg=C["text_primary"])

    def _notes_focus_out(self, _):
        if not self._notes.get("1.0", "end").strip():
            self._notes.insert("1.0", "What brings you here? Anything you'd like them to know…")
            self._notes.config(fg=C["text_secondary"])

    def _pick_day(self, day):
        self._selected_day.set(day)
        self._selected_slot = None
        for d, b in self._day_btns.items():
            b.config(bg=C["teal_600"] if d == day else C["bg_dark"])

        for w in self._slot_frame.winfo_children():
            w.destroy()

        avail = self.app.db.get_availability(self.tid)
        slots = avail.get(day, [])
        date_str = _next_date_for_day(day)

        self._slot_widgets = {}
        row = tk.Frame(self._slot_frame, bg=C["bg_card"]); row.pack(fill="x")
        for i, slot in enumerate(slots):
            if i % 4 == 0:
                row = tk.Frame(self._slot_frame, bg=C["bg_card"]); row.pack(fill="x", pady=(0, 8))
            booked = self.app.db.is_slot_booked(self.tid, date_str, slot)
            bg_col = C["bg_dark"] if booked else C["bg_dark"]
            fg_col = C["text_secondary"] if not booked else C["slate_400"]
            btn = tk.Button(row,
                text=_fmt_time(slot),
                state="disabled" if booked else "normal",
                command=lambda s=slot, d=date_str: self._pick_slot(s, d),
                bg=bg_col, fg=fg_col,
                disabledforeground=C["slate_500"],
                relief="flat", cursor="hand2" if not booked else "arrow",
                font=("Helvetica", FS["small"]), padx=14, pady=8,
                bd=1, highlightbackground=C["bg_card"])
            btn.pack(side="left", padx=(0, 8))
            if booked:
                tk.Label(btn.master, text="✕", fg=C["red_400"],
                    bg=bg_col, font=("Helvetica", 8)).place(relx=1, rely=0, anchor="ne")
            self._slot_widgets[slot] = btn

        if not slots:
            label(self._slot_frame, "No slots available on this day.",
                  size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(padx=4, pady=8)

        self._refresh_summary()

    def _pick_slot(self, slot, date_str):
        self._selected_slot = (date_str, slot)
        for s, b in self._slot_widgets.items():
            b.config(bg=C["teal_600"] if s == slot else C["bg_dark"],
                     fg=C["text_primary"] if s == slot else C["text_secondary"])
        self._refresh_summary()

    # ─── RIGHT: summary + confirm ────────────────────
    def _build_summary(self, parent):
        summ = card_frame(parent); summ.pack(fill="x", pady=(0, 16))
        label(summ, "Booking summary", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))
        self._summ_frame = tk.Frame(summ, bg=C["bg_card"])
        self._summ_frame.pack(fill="x", padx=16, pady=(0, 12))

        reminder_card = card_frame(parent); reminder_card.pack(fill="x", pady=(0, 16))
        label(reminder_card, "📅  Automated reminders", size="small", bold=True,
              color=C["teal_300"], bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 4))
        label(reminder_card,
              "• Email reminder: 24 hours before\n• SMS reminder: 1 hour before",
              size="small", color=C["text_secondary"], bg=C["bg_card"],
              justify="left").pack(anchor="w", padx=16, pady=(0, 12))

        self._confirm_btn = button(parent, "Proceed to payment →",
                                   self._go_to_payment, style="primary")
        self._confirm_btn.pack(fill="x", ipady=8)
        self._confirm_btn.config(state="disabled")
        self._err_lbl = label(parent, "", size="small", color=C["red_400"],
                              bg=C["bg_mid"])
        self._err_lbl.pack(pady=(8, 0))
        self._refresh_summary()

    def _refresh_summary(self, *_):
        for w in self._summ_frame.winfo_children():
            w.destroy()

        rows = [
            ("Therapist",    self.t["name"]),
            ("Title",        self.t.get("title", "—")),
        ]
        if self._selected_slot:
            date_str, slot = self._selected_slot
            d_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %d %B %Y")
            rows += [("Date", d_fmt), ("Time", _fmt_time(slot))]
        else:
            rows.append(("Date & Time", "Select a slot ↑"))

        rows += [
            ("Session type",  "🖥 Online" if self._session_type.get() == "online" else "🏢 In-person"),
            ("Amount",        f"KSh {self.t.get('price', 0):,}"),
        ]

        for k, v in rows:
            r = tk.Frame(self._summ_frame, bg=C["bg_card"]); r.pack(fill="x", pady=3)
            label(r, k, size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(side="left")
            label(r, v, size="small", bold=True,
                  bg=C["bg_card"]).pack(side="right")

        can_book = bool(self._selected_slot)
        self._confirm_btn.config(state="normal" if can_book else "disabled",
            bg=C["teal_600"] if can_book else C["bg_card"],
            fg=C["text_primary"] if can_book else C["text_secondary"])

    def _go_to_payment(self):
        user = self.app.current_user
        if not user:
            messagebox.showinfo("Sign in required", "Please sign in to book an appointment.")
            return
        if not self._selected_slot:
            self._err_lbl.config(text="Please select a time slot."); return

        # Re-check the slot hasn't just been taken before moving to payment
        date_str, slot = self._selected_slot
        if self.app.db.is_slot_booked(self.tid, date_str, slot):
            self._err_lbl.config(text="This slot was just taken. Please choose another.")
            self._pick_day(self._selected_day.get())
            return

        notes_txt = self._notes.get("1.0", "end").strip()
        if notes_txt == "What brings you here? Anything you'd like them to know…":
            notes_txt = ""

        booking_details = {
            "client_id":     user["id"],
            "therapist_id":  self.tid,
            "date":          date_str,
            "time":          slot,
            "type":          self._session_type.get(),
            "notes":         notes_txt,
            "amount":        self.t.get("price", 0),
        }
        self.app.show_payment(booking_details)
