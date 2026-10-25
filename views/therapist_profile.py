"""Therapist profile page — detailed view with availability and booking shortcut."""

import tkinter as tk
from tkinter import ttk
from views.styles import C, FS, label, button, card_frame, nav_bar


class TherapistProfileView(tk.Frame):
    def __init__(self, parent, app, therapist_id):
        super().__init__(parent, bg=C["bg_mid"])
        self.app = app
        self.tid = therapist_id
        self.t   = app.db.get_therapist_by_id(therapist_id)
        self._build()

    def _build(self):
        if not self.t:
            label(self, "Therapist not found.", size="h3").pack(pady=40)
            button(self, "← Back", self.app.show_find_therapist, style="ghost").pack()
            return

        nav_bar(self, self.app, show_back=True,
                back_cmd=self.app.show_find_therapist)

        # Scrollable body
        canvas = tk.Canvas(self, bg=C["bg_mid"], highlightthickness=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        body = tk.Frame(canvas, bg=C["bg_mid"])
        win  = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._build_hero(body)
        self._build_content(body)

    # ─── HERO ───────────────────────────────────────
    def _build_hero(self, parent):
        hero = tk.Frame(parent, bg=C["teal_900"])
        hero.pack(fill="x")

        inner = tk.Frame(hero, bg=C["teal_900"])
        inner.pack(padx=32, pady=24, fill="x")

        # Avatar
        initials = "".join(w[0] for w in self.t["name"].split()[:2]).upper()
        av = tk.Label(inner, text=initials, width=5, height=3,
                      bg=C["teal_700"], fg=C["white"],
                      font=("Helvetica", 22, "bold"))
        av.pack(side="left", padx=(0, 20))

        info = tk.Frame(inner, bg=C["teal_900"])
        info.pack(side="left", fill="x", expand=True)
        label(info, self.t["name"],  size="h2", bold=True,
              bg=C["teal_900"]).pack(anchor="w")
        label(info, self.t.get("title",""), size="body",
              color=C["teal_200"], bg=C["teal_900"]).pack(anchor="w", pady=(2, 6))

        meta = tk.Frame(info, bg=C["teal_900"]); meta.pack(anchor="w")
        for txt in [f"📍 {self.t.get('location','')}",
                    f"⭐ {self.t.get('rating', 0)} ({self.t.get('review_count', 0)} reviews)",
                    f"🌐 {self.t.get('languages','')}"]:
            label(meta, txt + "   ", size="small",
                  color=C["teal_200"], bg=C["teal_900"]).pack(side="left")

        # Price + CTA
        right = tk.Frame(inner, bg=C["teal_900"])
        right.pack(side="right", anchor="n")
        label(right, f"KSh {self.t.get('price', 0):,}", size="h2", bold=True,
              bg=C["teal_900"]).pack(anchor="e")
        label(right, "per session", size="small",
              color=C["teal_200"], bg=C["teal_900"]).pack(anchor="e", pady=(0, 12))
        button(right, "Book appointment →",
               lambda: self.app.show_book_appointment(self.tid),
               style="primary").pack(fill="x", ipady=6)
        button(right, "Join waitlist",
               self._join_waitlist,
               style="ghost").pack(fill="x", pady=(8, 0), ipady=4)

    # ─── CONTENT ────────────────────────────────────
    def _build_content(self, parent):
        cols = tk.Frame(parent, bg=C["bg_mid"])
        cols.pack(fill="both", expand=True, padx=24, pady=24)

        left = tk.Frame(cols, bg=C["bg_mid"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(cols, bg=C["bg_mid"], width=300)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        # ── About ────────────────────────────────────
        self._section_card(left, "About", self.t.get("about", "—"))

        # ── Specialities ─────────────────────────────
        sp_card = card_frame(left)
        sp_card.pack(fill="x", pady=(0, 16))
        label(sp_card, "Specialities", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 6))

        tag_row = tk.Frame(sp_card, bg=C["bg_card"])
        tag_row.pack(fill="x", padx=16, pady=(0, 12))
        for s in self.t.get("specialities", "").split(","):
            if s.strip():
                tk.Label(tag_row, text=f" {s.strip()} ",
                    bg=C["teal_900"], fg=C["teal_300"],
                    font=("Helvetica", FS["small"])).pack(side="left", padx=(0, 6), pady=2)

        row2 = tk.Frame(sp_card, bg=C["bg_card"]); row2.pack(fill="x", padx=16, pady=(0, 12))
        self._info_pair(row2, "Experience", self.t.get("experience", "—"))
        self._info_pair(row2, "Education",  self.t.get("education",  "—"))

        # ── Session types ─────────────────────────────
        st_card = card_frame(left)
        st_card.pack(fill="x", pady=(0, 16))
        label(st_card, "Session types", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 6))
        row3 = tk.Frame(st_card, bg=C["bg_card"]); row3.pack(fill="x", padx=16, pady=(0, 12))
        if self.t.get("online"):
            tk.Label(row3, text=" 🖥  Online / Video ", bg=C["bg_dark"],
                fg=C["text_secondary"],
                font=("Helvetica", FS["body"])).pack(side="left", padx=(0, 10))
        if self.t.get("in_person"):
            tk.Label(row3, text=" 🏢  In-person ", bg=C["bg_dark"],
                fg=C["text_secondary"],
                font=("Helvetica", FS["body"])).pack(side="left")
        label(st_card, f"Languages: {self.t.get('languages', '—')}",
              size="small", color=C["text_secondary"],
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(0, 12))

        # ── Insurance ────────────────────────────────
        ins_card = card_frame(left)
        ins_card.pack(fill="x", pady=(0, 16))
        label(ins_card, "Insurance & pricing", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 6))
        ins_row = tk.Frame(ins_card, bg=C["bg_card"]); ins_row.pack(fill="x", padx=16)
        for i in self.t.get("insurance", "").split(","):
            if i.strip():
                tk.Label(ins_row, text=f" {i.strip()} ",
                    bg=C["sage_100"], fg=C["sage_600"],
                    font=("Helvetica", FS["small"])).pack(side="left", padx=(0, 6), pady=2)
        if self.t.get("free_available"):
            label(ins_card,
                  "✓  Free sessions available for clients who cannot afford private care.",
                  size="small", color=C["green_400"], bg=C["bg_card"]).pack(
                  anchor="w", padx=16, pady=(8, 0))
        label(ins_card, f"Standard session: KSh {self.t.get('price', 0):,}",
              size="body", bold=True, bg=C["bg_card"]).pack(
              anchor="w", padx=16, pady=(8, 12))

        # ── RIGHT: availability ───────────────────────
        av_card = card_frame(right)
        av_card.pack(fill="x", pady=(0, 16))
        label(av_card, "Availability", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 8))

        avail = self.app.db.get_availability(self.tid)
        if avail:
            for day, slots in avail.items():
                label(av_card, day, size="small", bold=True,
                      color=C["teal_300"], bg=C["bg_card"]).pack(
                      anchor="w", padx=16, pady=(6, 2))
                slot_row = tk.Frame(av_card, bg=C["bg_card"])
                slot_row.pack(fill="x", padx=16, pady=(0, 4))
                for sl in slots:
                    h, m = sl.split(":")
                    h = int(h)
                    t12 = f"{h if h<=12 else h-12}:{m}{'AM' if h<12 else 'PM'}"
                    tk.Label(slot_row, text=f" {t12} ",
                        bg=C["bg_dark"], fg=C["text_secondary"],
                        font=("Helvetica", FS["small"])).pack(
                        side="left", padx=(0, 4), pady=2)
        else:
            label(av_card, "Contact to arrange availability.",
                  size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(0, 12))

        button(av_card, "Book a session →",
               lambda: self.app.show_book_appointment(self.tid),
               style="primary").pack(fill="x", padx=16, pady=(8, 16), ipady=6)

    def _section_card(self, parent, title, body_text):
        c = card_frame(parent)
        c.pack(fill="x", pady=(0, 16))
        label(c, title, size="h4", bold=True, bg=C["bg_card"]).pack(
            anchor="w", padx=16, pady=(12, 6))
        tk.Label(c, text=body_text, bg=C["bg_card"], fg=C["text_secondary"],
            font=("Helvetica", FS["body"]),
            wraplength=520, justify="left", anchor="w").pack(
            anchor="w", padx=16, pady=(0, 14))

    def _info_pair(self, parent, key, value):
        col = tk.Frame(parent, bg=C["bg_card"]); col.pack(side="left", padx=(0, 32))
        label(col, key, size="small", bold=True, color=C["text_secondary"],
              bg=C["bg_card"]).pack(anchor="w")
        label(col, value, size="body", bg=C["bg_card"]).pack(anchor="w", pady=(2, 0))

    def _join_waitlist(self):
        user = self.app.current_user
        if not user:
            tk.messagebox.showinfo("Sign in required",
                "Please sign in to join the waitlist.")
            return
        ok, err = self.app.db.add_to_waitlist(user["id"], self.tid)
        if ok:
            tk.messagebox.showinfo("Waitlist",
                f"You've been added to the waitlist for {self.t['name']}.\n"
                "You'll be notified when a slot becomes available.")
        else:
            tk.messagebox.showinfo("Waitlist", err)
