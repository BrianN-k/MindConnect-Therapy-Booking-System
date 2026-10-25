"""
Chart embedding helpers using matplotlib, themed to match the app's dark
teal palette.

Falls back to a simple text/bar placeholder if matplotlib (or its Tk
backend) isn't available in the environment, so the app never crashes —
it just asks the user to `pip install matplotlib` for full charts.
"""

import tkinter as tk
from views.styles import C, FS, label

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


# ── shared dark styling for all charts ──────────────────────────
def _style_axes(ax, fig):
    fig.patch.set_facecolor(C["bg_card"])
    ax.set_facecolor(C["bg_card"])
    ax.tick_params(colors=C["text_secondary"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(C["slate_700"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=C["slate_700"], linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)


def _fallback(parent, title, note="Install matplotlib for interactive charts:\npip install matplotlib"):
    f = tk.Frame(parent, bg=C["bg_card"])
    label(f, "📊", size="h1", bg=C["bg_card"]).pack(pady=(20, 6))
    label(f, title, size="h4", bold=True, bg=C["bg_card"]).pack()
    label(f, note, size="small", color=C["text_secondary"],
          bg=C["bg_card"], justify="center").pack(pady=(6, 20))
    return f


# ════════════════════════════════════════════════════════════════
def bar_chart(parent, categories, values, title="", ylabel="", color=None,
              figsize=(5.4, 3.2)):
    if not MATPLOTLIB_AVAILABLE:
        return _fallback(parent, title or "Bar chart")

    color = color or C["teal_400"]
    fig = Figure(figsize=figsize, dpi=96)
    ax = fig.add_subplot(111)
    _style_axes(ax, fig)

    bars = ax.bar(categories, values, color=color, width=0.55, zorder=3)
    if title:
        ax.set_title(title, color=C["text_primary"], fontsize=10, pad=10, loc="left")
    if ylabel:
        ax.set_ylabel(ylabel, color=C["text_secondary"], fontsize=8)
    ax.tick_params(axis="x", rotation=20)

    for b in bars:
        h = b.get_height()
        ax.annotate(f"{int(h):,}", (b.get_x() + b.get_width() / 2, h),
                    ha="center", va="bottom", fontsize=7.5, color=C["text_primary"])

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=C["bg_card"], highlightthickness=0)
    return widget


def line_chart(parent, x_labels, values, title="", ylabel="", color=None,
               figsize=(5.4, 3.2)):
    if not MATPLOTLIB_AVAILABLE:
        return _fallback(parent, title or "Line chart")

    color = color or C["teal_400"]
    fig = Figure(figsize=figsize, dpi=96)
    ax = fig.add_subplot(111)
    _style_axes(ax, fig)

    ax.plot(x_labels, values, color=color, linewidth=2.2, marker="o",
            markersize=5, markerfacecolor=C["teal_300"], markeredgewidth=0, zorder=3)
    ax.fill_between(range(len(x_labels)), values, color=color, alpha=0.12, zorder=2)

    if title:
        ax.set_title(title, color=C["text_primary"], fontsize=10, pad=10, loc="left")
    if ylabel:
        ax.set_ylabel(ylabel, color=C["text_secondary"], fontsize=8)
    ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=C["bg_card"], highlightthickness=0)
    return widget


def pie_chart(parent, labels, values, title="", colors=None, figsize=(4.6, 3.4)):
    if not MATPLOTLIB_AVAILABLE:
        return _fallback(parent, title or "Pie chart")

    palette = colors or [C["teal_400"], C["sage_400"], C["amber_400"],
                          C["red_400"], C["slate_400"], C["teal_200"]]
    fig = Figure(figsize=figsize, dpi=96)
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(C["bg_card"])

    # Filter out zero-value slices so the pie doesn't break
    filtered = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not filtered:
        return _fallback(parent, title or "Pie chart", note="No data yet.")
    f_labels, f_values = zip(*filtered)

    wedges, texts, autotexts = ax.pie(
        f_values, labels=f_labels, colors=palette[:len(f_values)],
        autopct="%1.0f%%", pctdistance=0.75, startangle=90,
        wedgeprops=dict(width=0.55, edgecolor=C["bg_card"], linewidth=2),
        textprops=dict(color=C["text_secondary"], fontsize=8.5)
    )
    for at in autotexts:
        at.set_color(C["text_primary"])
        at.set_fontsize(8)
        at.set_fontweight("bold")

    if title:
        ax.set_title(title, color=C["text_primary"], fontsize=10, pad=10)

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=C["bg_card"], highlightthickness=0)
    return widget
