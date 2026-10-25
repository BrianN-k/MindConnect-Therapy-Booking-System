"""
Centralised colour palette and widget factory for MindConnect.
All views import from here so a single change reskins everything.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont


# ── colour tokens ────────────────────────────────────────────────
C = {
    # backgrounds
    "bg_dark":       "#0D1F2D",   # root / sidebar
    "bg_mid":        "#132D3F",   # content area
    "bg_card":       "#1A3A52",   # cards
    "bg_light":      "#EAF5F6",   # light page bg
    "bg_white":      "#FFFFFF",

    # teal brand
    "teal_900":      "#052E36",
    "teal_700":      "#0D6478",
    "teal_600":      "#0F7D94",
    "teal_500":      "#1199B3",
    "teal_400":      "#29B6D0",
    "teal_300":      "#67D4E8",
    "teal_200":      "#A0DCE8",
    "teal_100":      "#D6F4F9",

    # sage green
    "sage_600":      "#3D7A65",
    "sage_400":      "#57A98E",
    "sage_100":      "#D4F0E7",

    # amber
    "amber_600":     "#B85A00",
    "amber_400":     "#E07B1F",
    "amber_100":     "#FDE8CB",

    # slate
    "slate_900":     "#0D1A22",
    "slate_700":     "#1F3344",
    "slate_500":     "#4A6478",
    "slate_400":     "#5C7A8F",
    "slate_300":     "#8AABBC",
    "slate_200":     "#C2D5DE",
    "slate_100":     "#E4EEF3",
    "slate_50":      "#F5F9FB",

    # status
    "red_400":       "#E05555",
    "red_100":       "#FDE8E8",
    "green_400":     "#3AAA6E",
    "green_100":     "#D4F4E4",

    "text_primary":  "#FFFFFF",
    "text_secondary":"#8AABBC",
    "text_dark":     "#0D1A22",
    "text_muted":    "#5C7A8F",

    # convenience aliases
    "white":         "#FFFFFF",
    "black":         "#000000",
}

# ── font sizes ────────────────────────────────────────────────────
FS = {
    "h1": 26, "h2": 20, "h3": 15, "h4": 12,
    "body": 11, "small": 9, "label": 10,
}


def apply_theme(root: tk.Tk):
    """Configure ttk styles and default fonts."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # ── ttk.Entry ────────────────────────────────────
    style.configure("TEntry",
        fieldbackground=C["bg_card"], foreground=C["text_primary"],
        insertcolor=C["teal_400"], borderwidth=1, relief="flat",
        padding=(8, 6)
    )
    style.map("TEntry",
        fieldbackground=[("focus", C["teal_900"]), ("active", C["bg_card"])],
        bordercolor=[("focus", C["teal_500"])]
    )

    # ── ttk.Combobox ─────────────────────────────────
    style.configure("TCombobox",
        fieldbackground=C["bg_card"], background=C["bg_card"],
        foreground=C["text_primary"], arrowcolor=C["teal_400"],
        selectbackground=C["teal_700"], selectforeground=C["text_primary"],
        padding=(8, 6)
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", C["bg_card"])],
        foreground=[("readonly", C["text_primary"])]
    )

    # ── ttk.Scrollbar ────────────────────────────────
    style.configure("Vertical.TScrollbar",
        background=C["bg_card"], troughcolor=C["bg_dark"],
        arrowcolor=C["slate_400"], borderwidth=0, relief="flat"
    )

    # ── ttk.Treeview ─────────────────────────────────
    style.configure("Treeview",
        background=C["bg_card"], fieldbackground=C["bg_card"],
        foreground=C["text_primary"], rowheight=36,
        borderwidth=0, relief="flat"
    )
    style.configure("Treeview.Heading",
        background=C["bg_dark"], foreground=C["text_secondary"],
        relief="flat", font=("Helvetica", FS["small"], "bold")
    )
    style.map("Treeview",
        background=[("selected", C["teal_700"])],
        foreground=[("selected", C["text_primary"])]
    )

    # ── ttk.Notebook ─────────────────────────────────
    style.configure("TNotebook",
        background=C["bg_dark"], borderwidth=0
    )
    style.configure("TNotebook.Tab",
        background=C["bg_card"], foreground=C["text_secondary"],
        padding=(16, 8), font=("Helvetica", FS["body"])
    )
    style.map("TNotebook.Tab",
        background=[("selected", C["teal_700"])],
        foreground=[("selected", C["text_primary"])]
    )

    # ── ttk.Scale ────────────────────────────────────
    style.configure("Horizontal.TScale",
        background=C["bg_mid"], troughcolor=C["bg_card"],
        sliderlength=18, sliderrelief="flat"
    )

    # ── ttk.Separator ────────────────────────────────
    style.configure("TSeparator", background=C["bg_card"])

    # ── ttk.Frame / LabelFrame ───────────────────────
    style.configure("TFrame",    background=C["bg_dark"])
    style.configure("Card.TFrame", background=C["bg_card"])
    style.configure("TLabelframe", background=C["bg_mid"], foreground=C["text_primary"])
    style.configure("TLabelframe.Label", background=C["bg_mid"], foreground=C["teal_400"], font=("Helvetica", FS["body"], "bold"))

    # ── ttk.Progressbar ──────────────────────────────
    style.configure("Teal.Horizontal.TProgressbar",
        troughcolor=C["bg_card"], background=C["teal_500"],
        thickness=8, borderwidth=0
    )


# ════════════════════════════════════════════════════════════════
# WIDGET FACTORIES
# ════════════════════════════════════════════════════════════════

def label(parent, text, size="body", bold=False, color=None, **kw):
    fg   = kw.pop("fg", None) or color or C["text_primary"]
    bg   = kw.pop("bg", parent.cget("bg") if hasattr(parent, "cget") else C["bg_dark"])
    font = kw.pop("font", None) or ("Helvetica", FS[size], "bold" if bold else "normal")
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


def entry(parent, textvariable=None, placeholder="", show=None, width=30, **kw):
    var = textvariable or tk.StringVar()
    e = ttk.Entry(parent, textvariable=var, show=show or "", width=width, **kw)

    def _add_placeholder():
        if placeholder and not var.get():
            e.insert(0, placeholder)
            e.config(foreground=C["slate_400"])

    def _on_focus_in(_):
        if e.get() == placeholder:
            e.delete(0, "end")
            e.config(foreground=C["text_primary"])

    def _on_focus_out(_):
        if not e.get():
            _add_placeholder()

    if placeholder:
        _add_placeholder()
        e.bind("<FocusIn>",  _on_focus_in)
        e.bind("<FocusOut>", _on_focus_out)

    return e, var


def button(parent, text, command=None, style="primary", width=None, **kw):
    colours = {
        "primary": (C["teal_600"],   C["teal_700"],   C["text_primary"]),
        "ghost":   (C["bg_card"],    C["bg_card"],     C["text_secondary"]),
        "danger":  (C["red_400"],    "#c44",           C["text_primary"]),
        "success": (C["sage_600"],   "#2d6350",        C["text_primary"]),
        "amber":   (C["amber_400"],  C["amber_600"],   C["text_primary"]),
        "dark":    (C["bg_dark"],    C["slate_700"],   C["text_primary"]),
    }
    bg, bg_h, fg = colours.get(style, colours["primary"])
    kw_btn = dict(
        text=text, command=command,
        bg=bg, fg=fg, activebackground=bg_h, activeforeground=fg,
        font=("Helvetica", FS["body"], "bold" if style == "primary" else "normal"),
        relief="flat", cursor="hand2", bd=0,
        padx=18, pady=9
    )
    if width: kw_btn["width"] = width
    kw_btn.update(kw)
    btn = tk.Button(parent, **kw_btn)
    btn.bind("<Enter>", lambda e: btn.config(bg=bg_h))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def card_frame(parent, **kw):
    """A rounded-looking card (as close as Tk allows)."""
    f = tk.Frame(parent, bg=C["bg_card"],
                 highlightbackground=C["teal_900"], highlightthickness=1,
                 **kw)
    return f


def separator(parent, orient="horizontal"):
    return ttk.Separator(parent, orient=orient)


def scrolled_text(parent, height=8, **kw):
    from tkinter import scrolledtext
    st = scrolledtext.ScrolledText(parent, height=height,
        bg=C["bg_card"], fg=C["text_primary"],
        insertbackground=C["teal_400"],
        font=("Helvetica", FS["body"]),
        relief="flat", borderwidth=0,
        wrap="word", **kw)
    return st


def status_badge(parent, status):
    colours = {
        "confirmed":  (C["green_100"], C["sage_600"]),
        "pending":    (C["amber_100"], C["amber_600"]),
        "cancelled":  (C["red_100"],   C["red_400"]),
        "completed":  (C["slate_100"], C["slate_500"]),
        "waitlisted": (C["teal_100"],  C["teal_700"]),
        "failed":     (C["red_100"],   C["red_400"]),
        "refunded":   (C["teal_100"],  C["teal_700"]),
    }
    bg, fg = colours.get(status, (C["slate_100"], C["slate_500"]))
    return tk.Label(parent, text=f"  {status}  ",
        bg=bg, fg=fg,
        font=("Helvetica", FS["small"], "bold"),
        relief="flat", padx=4, pady=2)


def nav_bar(parent, app, title="MindConnect", show_back=False, back_cmd=None):
    bar = tk.Frame(parent, bg=C["bg_dark"], height=56)
    bar.pack(fill="x")
    bar.pack_propagate(False)

    inner = tk.Frame(bar, bg=C["bg_dark"])
    inner.pack(fill="both", expand=True, padx=20)

    logo = tk.Label(inner, text="⊕  MindConnect", bg=C["bg_dark"],
        fg=C["teal_400"], font=("Helvetica", FS["h3"], "bold"), cursor="hand2")
    logo.pack(side="left", pady=12)
    logo.bind("<Button-1>", lambda e: app.show_client_dashboard() if app.current_user and app.current_user.get("role") == "client" else None)

    if show_back and back_cmd:
        btn = button(inner, "← Back", back_cmd, style="ghost", pady=4, padx=12)
        btn.pack(side="left", padx=12, pady=10)

    if app.current_user:
        tk.Label(inner, text=app.current_user["name"],
            bg=C["bg_dark"], fg=C["text_secondary"],
            font=("Helvetica", FS["small"])).pack(side="right", pady=12)
        button(inner, "Sign out", app.logout, style="ghost", pady=4, padx=12).pack(side="right", padx=8, pady=10)

    return bar


def sidebar_btn(parent, text, icon, command, active=False):
    bg = C["teal_700"] if active else C["bg_dark"]
    bg_h = C["teal_700"]
    fg = C["text_primary"] if active else C["text_secondary"]

    f = tk.Frame(parent, bg=bg, cursor="hand2")
    f.pack(fill="x")

    tk.Label(f, text=f"  {icon}  {text}", bg=bg, fg=fg,
        font=("Helvetica", FS["body"]),
        anchor="w", padx=8, pady=12).pack(fill="x")

    def _on_click(_=None):
        command()
    def _enter(_): f.config(bg=bg_h); [w.config(bg=bg_h) for w in f.winfo_children()]
    def _leave(_): f.config(bg=bg); [w.config(bg=bg) for w in f.winfo_children()]

    f.bind("<Button-1>", _on_click)
    for w in f.winfo_children():
        w.bind("<Button-1>", _on_click)
        w.bind("<Enter>", _enter)
        w.bind("<Leave>", _leave)
    f.bind("<Enter>", _enter)
    f.bind("<Leave>", _leave)
    return f
