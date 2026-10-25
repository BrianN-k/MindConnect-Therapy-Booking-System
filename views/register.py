"""Registration screen — client or therapist."""

import tkinter as tk
from tkinter import ttk, messagebox
from views.styles import C, FS, label, entry, button, card_frame


class RegisterView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_dark"])
        self.app = app
        self._role = tk.StringVar(value="client")
        self._build()

    def _build(self):
        # ── scrollable canvas ──────────────────────
        canvas = tk.Canvas(self, bg=C["bg_dark"], highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=C["bg_dark"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.itemconfig(win_id, width=canvas.winfo_width())
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", _resize)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        # ── content ────────────────────────────────
        form = tk.Frame(inner, bg=C["bg_dark"])
        form.pack(expand=True, pady=40, padx=40)

        label(form, "⊕  MindConnect", size="h3", bold=True, color=C["teal_400"]).pack(pady=(0, 4))
        label(form, "Create your account", size="h2", bold=True).pack()
        label(form, "Free to join. Start finding help today.", size="body",
              color=C["text_secondary"]).pack(pady=(4, 24))

        # ── role toggle ────────────────────────────
        role_row = tk.Frame(form, bg=C["bg_card"], bd=0)
        role_row.pack(fill="x", pady=(0, 24), ipady=4, ipadx=4)
        for r, txt in [("client", "👤  I'm a Client"), ("therapist", "🩺  I'm a Therapist")]:
            b = tk.Button(role_row, text=txt, command=lambda v=r: self._switch_role(v),
                bg=C["teal_600"] if r == "client" else C["bg_card"],
                fg=C["text_primary"], relief="flat", cursor="hand2",
                font=("Helvetica", FS["body"], "bold"), padx=24, pady=10)
            b.pack(side="left", expand=True, fill="x")
            setattr(self, f"_rbtn_{r}", b)

        self._err = label(form, "", size="small", color=C["red_400"])
        self._err.pack()

        # ── name row ───────────────────────────────
        row = tk.Frame(form, bg=C["bg_dark"]); row.pack(fill="x", pady=(8, 0))
        left_col = tk.Frame(row, bg=C["bg_dark"]); left_col.pack(side="left", expand=True, fill="x", padx=(0, 8))
        right_col = tk.Frame(row, bg=C["bg_dark"]); right_col.pack(side="left", expand=True, fill="x")
        label(left_col, "First name", size="label", color=C["text_secondary"]).pack(anchor="w")
        self._fn_entry, self._fn = entry(left_col, placeholder="Amina")
        self._fn_entry.pack(fill="x", pady=(4, 12), ipady=4)
        label(right_col, "Last name", size="label", color=C["text_secondary"]).pack(anchor="w")
        self._ln_entry, self._ln = entry(right_col, placeholder="Odhiambo")
        self._ln_entry.pack(fill="x", pady=(4, 12), ipady=4)

        # ── email & phone ──────────────────────────
        for lbl_txt, attr, ph in [
            ("Email address", "_email", "you@example.com"),
            ("Phone number",  "_phone", "+254 7XX XXX XXX"),
        ]:
            label(form, lbl_txt, size="label", color=C["text_secondary"]).pack(anchor="w")
            e, v = entry(form, placeholder=ph, width=40)
            e.pack(fill="x", pady=(4, 12), ipady=4)
            setattr(self, f"{attr}_entry", e)
            setattr(self, attr, v)

        # ── therapist-specific fields ──────────────
        self._th_frame = tk.Frame(form, bg=C["bg_dark"])
        self._th_frame.pack(fill="x")
        self._build_therapist_fields(self._th_frame)
        self._th_frame.pack_forget()   # hidden by default

        # ── password ───────────────────────────────
        for lbl_txt, attr, ph in [
            ("Password",         "_pw",   "At least 6 characters"),
            ("Confirm password", "_pw2",  "Repeat password"),
        ]:
            label(form, lbl_txt, size="label", color=C["text_secondary"]).pack(anchor="w")
            e, v = entry(form, show="•", placeholder=ph, width=40)
            e.pack(fill="x", pady=(4, 12), ipady=4)
            setattr(self, f"{attr}_entry", e)
            setattr(self, attr, v)

        # ── T&C ────────────────────────────────────
        self._terms = tk.BooleanVar(value=False)
        tc_row = tk.Frame(form, bg=C["bg_dark"]); tc_row.pack(anchor="w", pady=(4, 20))
        tk.Checkbutton(tc_row, variable=self._terms,
            bg=C["bg_dark"], fg=C["text_secondary"],
            selectcolor=C["teal_700"], activebackground=C["bg_dark"],
            font=("Helvetica", FS["body"])).pack(side="left")
        label(tc_row, "I agree to the Terms of Service and Privacy Policy",
              size="body", color=C["text_secondary"]).pack(side="left")

        button(form, "Create account →", self._register, style="primary", width=38).pack(ipady=4)

        reg_row = tk.Frame(form, bg=C["bg_dark"]); reg_row.pack(pady=(12, 0))
        label(reg_row, "Already have an account?  ", size="body", color=C["text_secondary"]).pack(side="left")
        lk = tk.Label(reg_row, text="Sign in", bg=C["bg_dark"], fg=C["teal_400"],
            font=("Helvetica", FS["body"], "underline"), cursor="hand2")
        lk.pack(side="left")
        lk.bind("<Button-1>", lambda e: self.app.show_login())

    def _build_therapist_fields(self, parent):
        label(parent, "Professional title", size="label", color=C["text_secondary"]).pack(anchor="w")
        self._title_entry, self._title = entry(parent, placeholder="Clinical Psychologist", width=40)
        self._title_entry.pack(fill="x", pady=(4, 12), ipady=4)

        row = tk.Frame(parent, bg=C["bg_dark"]); row.pack(fill="x")
        lc = tk.Frame(row, bg=C["bg_dark"]); lc.pack(side="left", expand=True, fill="x", padx=(0,8))
        rc = tk.Frame(row, bg=C["bg_dark"]); rc.pack(side="left", expand=True, fill="x")

        label(lc, "Session price (KSh)", size="label", color=C["text_secondary"]).pack(anchor="w")
        self._price_entry, self._price = entry(lc, placeholder="2500")
        self._price_entry.pack(fill="x", pady=(4, 12), ipady=4)

        label(rc, "Location", size="label", color=C["text_secondary"]).pack(anchor="w")
        self._loc_entry, self._loc = entry(rc, placeholder="Westlands, Nairobi")
        self._loc_entry.pack(fill="x", pady=(4, 12), ipady=4)

        self._free_var = tk.BooleanVar()
        fr = tk.Frame(parent, bg=C["bg_dark"]); fr.pack(anchor="w", pady=(0, 12))
        tk.Checkbutton(fr, variable=self._free_var, bg=C["bg_dark"],
            selectcolor=C["teal_700"], activebackground=C["bg_dark"]).pack(side="left")
        label(fr, "I offer free sessions for clients who cannot afford care",
              size="body", color=C["text_secondary"]).pack(side="left")

    def _switch_role(self, role):
        self._role.set(role)
        for r in ("client", "therapist"):
            btn = getattr(self, f"_rbtn_{r}")
            btn.config(bg=C["teal_600"] if r == role else C["bg_card"])
        if role == "therapist":
            self._th_frame.pack(fill="x")
        else:
            self._th_frame.pack_forget()

    def _register(self):
        fn   = self._fn.get().strip()
        ln   = self._ln.get().strip()
        email = self._email.get().strip()
        phone = self._phone.get().strip()
        pw   = self._pw.get().strip()
        pw2  = self._pw2.get().strip()
        role = self._role.get()

        # Validation
        if not fn or fn == "Amina": self._err.config(text="First name is required."); return
        if not ln or ln == "Odhiambo": self._err.config(text="Last name is required."); return
        if "@" not in email: self._err.config(text="Enter a valid email."); return
        if len(pw) < 6: self._err.config(text="Password must be at least 6 characters."); return
        if pw != pw2: self._err.config(text="Passwords do not match."); return
        if not self._terms.get(): self._err.config(text="You must accept the terms."); return

        uid, err = self.app.db.create_user(f"{fn} {ln}", email, pw, role, phone)
        if err:
            self._err.config(text=err); return

        if role == "therapist":
            try:
                price = int(self._price.get().strip() or 0)
            except ValueError:
                price = 0
            self.app.db.create_therapist_profile(uid,
                title=self._title.get().strip(),
                location=self._loc.get().strip(),
                price=price,
                free_available=1 if self._free_var.get() else 0
            )

        self.app.current_user = self.app.db.get_user_by_id(uid)
        messagebox.showinfo("Account Created", f"Welcome to MindConnect, {fn}!")
        self.app.navigate_after_login()
