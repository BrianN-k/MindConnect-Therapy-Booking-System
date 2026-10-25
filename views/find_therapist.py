"""Find Therapist — searchable, filterable therapist directory."""

import tkinter as tk
from tkinter import ttk
from views.styles import C, FS, label, button, card_frame, entry, nav_bar, separator


class FindTherapistView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_mid"])
        self.app = app
        self._therapists = []
        self._build()
        self._load()

    # ════════════════════════════════════════════════
    # BUILD
    # ════════════════════════════════════════════════
    def _build(self):
        nav_bar(self, self.app, show_back=True,
                back_cmd=lambda: self.app.navigate_after_login())

        # ── page header ─────────────────────────────
        hdr = tk.Frame(self, bg=C["bg_dark"])
        hdr.pack(fill="x")
        label(hdr, "Find a Therapist", size="h2", bold=True,
              bg=C["bg_dark"]).pack(padx=24, pady=(20, 4))
        label(hdr, "Browse licensed professionals matched to your needs",
              size="body", color=C["text_secondary"],
              bg=C["bg_dark"]).pack(padx=24, pady=(0, 16))

        # ── search bar ──────────────────────────────
        sb_frame = tk.Frame(self, bg=C["bg_dark"])
        sb_frame.pack(fill="x", padx=24, pady=(0, 16))

        self._search_entry, self._search_var = entry(
            sb_frame, placeholder="Search by name, speciality, or location…", width=50)
        self._search_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        self._search_var.trace_add("write", lambda *_: self._apply_filters())

        button(sb_frame, "🔍  Search", self._apply_filters, style="primary").pack(side="left", ipady=6)

        # ── body: sidebar + results ──────────────────
        body = tk.Frame(self, bg=C["bg_mid"])
        body.pack(fill="both", expand=True, padx=0)

        # Sidebar filters
        self._sidebar = tk.Frame(body, bg=C["bg_dark"], width=230)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._build_filters(self._sidebar)

        # Results pane
        results_outer = tk.Frame(body, bg=C["bg_mid"])
        results_outer.pack(side="left", fill="both", expand=True)

        meta_bar = tk.Frame(results_outer, bg=C["bg_mid"])
        meta_bar.pack(fill="x", padx=20, pady=(14, 8))
        self._count_lbl = label(meta_bar, "Loading…", size="small",
                                color=C["text_secondary"], bg=C["bg_mid"])
        self._count_lbl.pack(side="left")

        sort_row = tk.Frame(meta_bar, bg=C["bg_mid"])
        sort_row.pack(side="right")
        label(sort_row, "Sort: ", size="small", color=C["text_secondary"],
              bg=C["bg_mid"]).pack(side="left")
        self._sort_var = tk.StringVar(value="rating")
        sort_cb = ttk.Combobox(sort_row, textvariable=self._sort_var, width=16,
                               state="readonly",
                               values=["rating", "price: low→high",
                                       "price: high→low", "most reviews"])
        sort_cb.pack(side="left")
        sort_cb.bind("<<ComboboxSelected>>", lambda _: self._apply_filters())

        # Scrollable results
        canvas = tk.Canvas(results_outer, bg=C["bg_mid"], highlightthickness=0)
        vsb = ttk.Scrollbar(results_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=(20, 0))

        self._res_frame = tk.Frame(canvas, bg=C["bg_mid"])
        win_id = canvas.create_window((0, 0), window=self._res_frame, anchor="nw")

        def _resize(e):
            canvas.itemconfig(win_id, width=canvas.winfo_width())
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", _resize)
        self._res_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    # ════════════════════════════════════════════════
    # FILTERS SIDEBAR
    # ════════════════════════════════════════════════
    def _build_filters(self, parent):
        label(parent, "  Filters", size="h4", bold=True, color=C["text_primary"],
              bg=C["bg_dark"]).pack(anchor="w", pady=(16, 8))

        # Scrollable sidebar
        c = tk.Canvas(parent, bg=C["bg_dark"], highlightthickness=0)
        c.pack(fill="both", expand=True)
        inner = tk.Frame(c, bg=C["bg_dark"])
        c.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))

        def section(title):
            tk.Frame(inner, bg=C["bg_card"], height=1).pack(fill="x", padx=12, pady=(12, 8))
            label(inner, title, size="small", bold=True,
                  color=C["text_secondary"], bg=C["bg_dark"]).pack(anchor="w", padx=16)

        # ── speciality ──────────────────────────────
        section("SPECIALITY")
        self._spec_vars = {}
        for s in ["Anxiety", "Depression", "CBT", "Trauma", "Relationships",
                  "Grief", "Addiction", "Youth", "Family Therapy", "Stress"]:
            v = tk.BooleanVar()
            self._spec_vars[s] = v
            r = tk.Frame(inner, bg=C["bg_dark"]); r.pack(fill="x", padx=16, pady=2)
            tk.Checkbutton(r, variable=v, command=self._apply_filters,
                bg=C["bg_dark"], selectcolor=C["teal_700"],
                activebackground=C["bg_dark"]).pack(side="left")
            label(r, s, size="body", bg=C["bg_dark"]).pack(side="left")

        # ── price ───────────────────────────────────
        section("MAX PRICE (KSh)")
        self._price_var = tk.IntVar(value=5000)
        self._price_lbl = label(inner, "KSh 5,000+", size="small",
                                color=C["teal_300"], bg=C["bg_dark"])
        self._price_lbl.pack(anchor="w", padx=16)
        sl = ttk.Scale(inner, from_=0, to=5000, variable=self._price_var,
                       orient="horizontal", command=self._on_price_change)
        sl.pack(fill="x", padx=16, pady=(4, 0))

        # ── session type ─────────────────────────────
        section("SESSION TYPE")
        self._online_var  = tk.BooleanVar()
        self._inpers_var  = tk.BooleanVar()
        for txt, v in [("🖥  Online / Video", self._online_var),
                       ("🏢  In-person",       self._inpers_var)]:
            r = tk.Frame(inner, bg=C["bg_dark"]); r.pack(fill="x", padx=16, pady=2)
            tk.Checkbutton(r, variable=v, command=self._apply_filters,
                bg=C["bg_dark"], selectcolor=C["teal_700"],
                activebackground=C["bg_dark"]).pack(side="left")
            label(r, txt, size="body", bg=C["bg_dark"]).pack(side="left")

        # ── language ─────────────────────────────────
        section("LANGUAGE")
        self._lang_vars = {}
        for lng in ["English", "Swahili", "Luo", "Arabic", "Kikuyu"]:
            v = tk.BooleanVar()
            self._lang_vars[lng] = v
            r = tk.Frame(inner, bg=C["bg_dark"]); r.pack(fill="x", padx=16, pady=2)
            tk.Checkbutton(r, variable=v, command=self._apply_filters,
                bg=C["bg_dark"], selectcolor=C["teal_700"],
                activebackground=C["bg_dark"]).pack(side="left")
            label(r, lng, size="body", bg=C["bg_dark"]).pack(side="left")

        # ── insurance ────────────────────────────────
        section("INSURANCE")
        self._ins_vars = {}
        for ins in ["NHIF", "AAR", "Jubilee", "Britam", "Madison"]:
            v = tk.BooleanVar()
            self._ins_vars[ins] = v
            r = tk.Frame(inner, bg=C["bg_dark"]); r.pack(fill="x", padx=16, pady=2)
            tk.Checkbutton(r, variable=v, command=self._apply_filters,
                bg=C["bg_dark"], selectcolor=C["teal_700"],
                activebackground=C["bg_dark"]).pack(side="left")
            label(r, ins, size="body", bg=C["bg_dark"]).pack(side="left")

        # ── free only ────────────────────────────────
        section("OTHER")
        self._free_var = tk.BooleanVar()
        r = tk.Frame(inner, bg=C["bg_dark"]); r.pack(fill="x", padx=16, pady=2)
        tk.Checkbutton(r, variable=self._free_var, command=self._apply_filters,
            bg=C["bg_dark"], selectcolor=C["teal_700"],
            activebackground=C["bg_dark"]).pack(side="left")
        label(r, "Free sessions available", size="body", bg=C["bg_dark"]).pack(side="left")

        # ── clear ────────────────────────────────────
        button(inner, "Clear all filters", self._clear_filters,
               style="ghost").pack(fill="x", padx=16, pady=16)

    # ════════════════════════════════════════════════
    # DATA
    # ════════════════════════════════════════════════
    def _load(self):
        self._therapists = self.app.db.get_all_therapists()
        self._apply_filters()

    def _on_price_change(self, val):
        v = int(float(val))
        self._price_lbl.config(
            text="KSh 5,000+" if v >= 4999 else f"KSh {v:,}")
        self._apply_filters()

    def _clear_filters(self):
        for v in self._spec_vars.values(): v.set(False)
        for v in self._lang_vars.values(): v.set(False)
        for v in self._ins_vars.values():  v.set(False)
        self._online_var.set(False)
        self._inpers_var.set(False)
        self._free_var.set(False)
        self._price_var.set(5000)
        self._price_lbl.config(text="KSh 5,000+")
        self._search_var.set("")
        self._apply_filters()

    def _apply_filters(self, *_):
        q     = self._search_var.get().strip()
        # avoid placeholder text being treated as query
        if q in ("Search by name, speciality, or location…", ""): q = ""

        sel_specs = [k for k, v in self._spec_vars.items() if v.get()]
        sel_langs = [k for k, v in self._lang_vars.items() if v.get()]
        sel_ins   = [k for k, v in self._ins_vars.items()  if v.get()]
        max_price = self._price_var.get()
        online_only = self._online_var.get()
        inpers_only = self._inpers_var.get()
        free_only   = self._free_var.get()

        results = []
        for t in self._therapists:
            # text search
            if q:
                haystack = " ".join([
                    t.get("name", ""), t.get("specialities", ""),
                    t.get("location", ""), t.get("title", "")
                ]).lower()
                if q.lower() not in haystack:
                    continue
            # price
            if max_price < 4999 and t.get("price", 0) > max_price:
                continue
            # speciality
            specs = t.get("specialities", "")
            if sel_specs and not any(s.lower() in specs.lower() for s in sel_specs):
                continue
            # session type
            if online_only and not t.get("online"):
                continue
            if inpers_only and not t.get("in_person"):
                continue
            # language
            langs = t.get("languages", "")
            if sel_langs and not any(l in langs for l in sel_langs):
                continue
            # insurance
            ins = t.get("insurance", "")
            if sel_ins and not any(i in ins for i in sel_ins):
                continue
            # free
            if free_only and not t.get("free_available"):
                continue
            results.append(t)

        # sort
        sort = self._sort_var.get()
        if sort == "rating":
            results.sort(key=lambda t: -float(t.get("rating", 0)))
        elif "low→high" in sort:
            results.sort(key=lambda t: t.get("price", 0))
        elif "high→low" in sort:
            results.sort(key=lambda t: -t.get("price", 0))
        elif "reviews" in sort:
            results.sort(key=lambda t: -t.get("review_count", 0))

        self._render_results(results)

    # ════════════════════════════════════════════════
    # RENDER CARDS
    # ════════════════════════════════════════════════
    def _render_results(self, therapists):
        for w in self._res_frame.winfo_children():
            w.destroy()

        n = len(therapists)
        self._count_lbl.config(text=f"Showing {n} therapist{'s' if n != 1 else ''}")

        if not therapists:
            empty = tk.Frame(self._res_frame, bg=C["bg_mid"])
            empty.pack(expand=True, pady=60)
            label(empty, "🔍", size="h1", bg=C["bg_mid"]).pack()
            label(empty, "No therapists found", size="h3",
                  bg=C["bg_mid"]).pack(pady=(12, 6))
            label(empty, "Try adjusting your filters or search term.",
                  size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack()
            return

        # 2-column grid
        col = 0
        row_frame = None
        for t in therapists:
            if col % 2 == 0:
                row_frame = tk.Frame(self._res_frame, bg=C["bg_mid"])
                row_frame.pack(fill="x", pady=(0, 16))
            self._make_card(row_frame, t)
            col += 1

    def _make_card(self, parent, t):
        card = card_frame(parent)
        card.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=0)

        # ── header ──────────────────────────────────
        hdr = tk.Frame(card, bg=C["bg_card"])
        hdr.pack(fill="x", padx=16, pady=(16, 0))

        # Avatar
        initials = "".join(w[0] for w in t.get("name", "??").split()[:2]).upper()
        av = tk.Label(hdr, text=initials, width=4, height=2,
                      bg=C["teal_700"], fg=C["text_primary"],
                      font=("Helvetica", FS["h4"], "bold"))
        av.pack(side="left")

        info = tk.Frame(hdr, bg=C["bg_card"])
        info.pack(side="left", padx=12, fill="x", expand=True)
        label(info, t.get("name", ""), size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w")
        label(info, t.get("title", ""), size="small",
              color=C["teal_300"], bg=C["bg_card"]).pack(anchor="w")
        label(info, f"📍 {t.get('location', '')}", size="small",
              color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w")

        rating = t.get("rating", 0)
        reviews = t.get("review_count", 0)
        label(hdr, f"⭐ {rating} ({reviews})", size="small",
              color=C["amber_400"], bg=C["bg_card"],
              bold=True).pack(side="right", anchor="n")

        # ── tags ────────────────────────────────────
        specs = t.get("specialities", "").split(",")
        tag_row = tk.Frame(card, bg=C["bg_card"])
        tag_row.pack(fill="x", padx=16, pady=(10, 0))
        for i, s in enumerate(specs[:4]):
            tk.Label(tag_row, text=f" {s.strip()} ",
                bg=C["teal_900"], fg=C["teal_300"],
                font=("Helvetica", FS["small"]),
                relief="flat", padx=2, pady=2).pack(side="left", padx=(0, 4))

        # ── session types ────────────────────────────
        type_row = tk.Frame(card, bg=C["bg_card"])
        type_row.pack(fill="x", padx=16, pady=6)
        if t.get("online"):
            tk.Label(type_row, text=" 🖥 Online ", bg=C["bg_dark"],
                fg=C["text_secondary"],
                font=("Helvetica", FS["small"])).pack(side="left", padx=(0, 6))
        if t.get("in_person"):
            tk.Label(type_row, text=" 🏢 In-person ", bg=C["bg_dark"],
                fg=C["text_secondary"],
                font=("Helvetica", FS["small"])).pack(side="left")
        if t.get("free_available"):
            tk.Label(type_row, text=" FREE available ",
                bg=C["green_100"], fg=C["sage_600"],
                font=("Helvetica", FS["small"], "bold")).pack(side="right")

        # ── language & insurance ─────────────────────
        label(card, f"🌐  {t.get('languages', '')}",
              size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(
              anchor="w", padx=16)

        # ── footer ──────────────────────────────────
        foot = tk.Frame(card, bg=C["slate_900"])
        foot.pack(fill="x", padx=0, pady=(12, 0), ipady=10)
        tk.Frame(card, bg=C["slate_900"], height=1).pack(fill="x")

        price = t.get("price", 0)
        label(foot, f"KSh {price:,} / session",
              size="body", bold=True, bg=C["slate_900"]).pack(side="left", padx=16)

        tid = t.get("id", "")
        btn_row = tk.Frame(foot, bg=C["slate_900"])
        btn_row.pack(side="right", padx=16)
        button(btn_row, "View profile",
               lambda _id=tid: self.app.show_therapist_profile(_id),
               style="primary").pack(side="left", padx=(0, 8), ipady=2)
        button(btn_row, "Book →",
               lambda _id=tid: self.app.show_book_appointment(_id),
               style="ghost").pack(side="left", ipady=2)
