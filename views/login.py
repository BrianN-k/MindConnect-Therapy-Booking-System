"""Login screen."""

import tkinter as tk
from tkinter import messagebox
from views.styles import C, FS, label, entry, button, card_frame


class LoginView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_dark"])
        self.app = app
        self._build()

    def _build(self):
        # ── left panel (branding) ──────────────────
        left = tk.Frame(self, bg=C["teal_900"], width=420)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Frame(left, bg=C["teal_900"]).pack(expand=True)   # spacer

        label(left, "⊕", size="h1", bold=True, color=C["teal_400"],
              bg=C["teal_900"]).pack(pady=(0, 8))
        label(left, "MindConnect", size="h1", bold=True, color=C["text_primary"],
              bg=C["teal_900"]).pack()
        label(left, "Mental Health &\nTherapist Booking", size="h3", color=C["teal_200"],
              bg=C["teal_900"], justify="center").pack(pady=(8, 32))

        for stat, lbl in [("970M", "people affected globally"),
                           ("1 in 10", "Kenyans need support"),
                           ("56%", "faster with digital booking")]:
            f = tk.Frame(left, bg=C["teal_900"])
            f.pack(pady=4, padx=40, fill="x")
            label(f, stat, size="h2", bold=True, color=C["teal_300"], bg=C["teal_900"]).pack(side="left")
            label(f, f"  {lbl}", size="small", color=C["teal_200"], bg=C["teal_900"]).pack(side="left", pady=2)

        tk.Frame(left, bg=C["teal_900"]).pack(expand=True)   # spacer

        label(left, "© 2026 KCA University · STU 3101",
              size="small", color=C["teal_700"], bg=C["teal_900"]).pack(pady=16)

        # ── right panel (form) ──────────────────────
        right = tk.Frame(self, bg=C["bg_dark"])
        right.pack(side="left", fill="both", expand=True)

        form_outer = tk.Frame(right, bg=C["bg_dark"])
        form_outer.place(relx=0.5, rely=0.5, anchor="center")

        label(form_outer, "Welcome back", size="h2", bold=True).pack(anchor="w")
        label(form_outer, "Sign in to your account", size="body",
              color=C["text_secondary"]).pack(anchor="w", pady=(4, 24))

        # ── demo hint ──────────────────────────────
        hint = card_frame(form_outer)
        hint.pack(fill="x", pady=(0, 20), ipadx=12, ipady=10)
        label(hint, "🔑  Demo accounts (click to fill)", size="small",
              color=C["teal_400"], bg=C["bg_card"]).pack(anchor="w", padx=12, pady=(8, 4))
        demos = [
            ("Client",    "amina@example.com",     "pass123"),
            ("Therapist", "sarah@example.com",      "pass123"),
            ("Admin",     "admin@mindconnect.ke",   "admin123"),
        ]
        for role, em, pw in demos:
            lk = tk.Label(hint,
                text=f"  {role}: {em}  /  {pw}",
                bg=C["bg_card"], fg=C["teal_300"],
                font=("Helvetica", FS["small"]), cursor="hand2", anchor="w")
            lk.pack(fill="x", padx=12, pady=1)
            lk.bind("<Button-1>", lambda e, email=em, p=pw: self._fill_demo(email, p))

        # ── email ──────────────────────────────────
        label(form_outer, "Email address", size="label",
              color=C["text_secondary"]).pack(anchor="w")
        self._email_entry, self._email_var = entry(form_outer, placeholder="you@example.com", width=40)
        self._email_entry.pack(fill="x", pady=(4, 14), ipady=4)

        # ── password ───────────────────────────────
        label(form_outer, "Password", size="label", color=C["text_secondary"]).pack(anchor="w")
        self._pw_entry, self._pw_var = entry(form_outer, show="•", placeholder="••••••••", width=40)
        self._pw_entry.pack(fill="x", pady=(4, 20), ipady=4)
        self._pw_entry.bind("<Return>", lambda e: self._login())

        button(form_outer, "Sign in →", self._login, style="primary", width=38).pack(pady=(0, 14), ipady=4)

        # ── register link ──────────────────────────
        row = tk.Frame(form_outer, bg=C["bg_dark"])
        row.pack()
        label(row, "Don't have an account? ", size="body", color=C["text_secondary"]).pack(side="left")
        lk = tk.Label(row, text="Create one free", bg=C["bg_dark"], fg=C["teal_400"],
            font=("Helvetica", FS["body"], "underline"), cursor="hand2")
        lk.pack(side="left")
        lk.bind("<Button-1>", lambda e: self.app.show_register())

        self._err_lbl = label(form_outer, "", size="small", color=C["red_400"])
        self._err_lbl.pack(pady=(10, 0))

    def _fill_demo(self, email, password):
        self._email_var.set(email)
        self._pw_var.set(password)
        # clear placeholder styling
        self._email_entry.config(foreground=C["text_primary"])
        self._pw_entry.config(foreground=C["text_primary"])

    def _login(self):
        email = self._email_var.get().strip()
        pw    = self._pw_var.get().strip()

        if not email or email == "you@example.com":
            self._err_lbl.config(text="Please enter your email address."); return
        if not pw or pw == "••••••••":
            self._err_lbl.config(text="Please enter your password."); return

        user = self.app.db.login(email, pw)
        if not user:
            self._err_lbl.config(text="Invalid email or password. Please try again.")
            return

        self.app.current_user = user
        self.app.navigate_after_login()
