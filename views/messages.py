"""Secure messaging between clients and therapists."""

import tkinter as tk
from tkinter import ttk
from views.styles import C, FS, label, button, nav_bar
from datetime import datetime


def _fmt_ts(ts):
    try:
        dt = datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
        return dt.strftime("%d %b, %H:%M")
    except Exception:
        return ts or ""


class MessagesView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg_mid"])
        self.app = app
        self.user = app.current_user
        self._active_contact = getattr(app, "messages_target", None)
        self._build()

    def _build(self):
        nav_bar(self, self.app, show_back=True,
                back_cmd=self.app.navigate_after_login)

        hdr = tk.Frame(self, bg=C["bg_dark"]); hdr.pack(fill="x")
        label(hdr, "Messages", size="h2", bold=True, bg=C["bg_dark"]).pack(
            padx=24, pady=(20, 4), anchor="w")
        label(hdr, "Secure, private communication with your care team",
              size="body", color=C["text_secondary"],
              bg=C["bg_dark"]).pack(padx=24, pady=(0, 16), anchor="w")

        body = tk.Frame(self, bg=C["bg_mid"]); body.pack(fill="both", expand=True)

        # ── contact list ─────────────────────────────
        self._contact_panel = tk.Frame(body, bg=C["bg_dark"], width=260)
        self._contact_panel.pack(side="left", fill="y")
        self._contact_panel.pack_propagate(False)

        contacts = self.app.db.get_conversations_for_user(self.user["id"])
        # If therapist has no prior messages but has clients, list them too
        if self.user["role"] == "therapist":
            th = self.app.db.get_therapist_by_user(self.user["id"])
            if th:
                apts = self.app.db.get_appointments_for_therapist(th["id"])
                for a in apts:
                    c = self.app.db.get_user_by_id(a["client_id"])
                    if c and c["id"] not in [x["id"] for x in contacts]:
                        contacts.append(c)
        elif self.user["role"] == "client":
            apts = self.app.db.get_appointments_for_client(self.user["id"])
            for a in apts:
                th = self.app.db.get_therapist_by_id(a["therapist_id"])
                if th:
                    tu = self.app.db.get_user_by_id(th["user_id"])
                    if tu and tu["id"] not in [x["id"] for x in contacts]:
                        contacts.append(tu)

        if not self._active_contact and contacts:
            self._active_contact = contacts[0]["id"]

        if not contacts:
            empty = tk.Frame(self._contact_panel, bg=C["bg_dark"])
            empty.pack(expand=True)
            label(empty, "No conversations yet.", size="body",
                  color=C["text_secondary"], bg=C["bg_dark"]).pack(pady=40, padx=16)
        else:
            for c in contacts:
                self._contact_row(c)

        # ── thread panel ─────────────────────────────
        self._thread_panel = tk.Frame(body, bg=C["bg_mid"])
        self._thread_panel.pack(side="left", fill="both", expand=True)

        if self._active_contact:
            self._render_thread(self._active_contact)
        else:
            label(self._thread_panel, "Select a conversation to begin.",
                  size="body", color=C["text_secondary"],
                  bg=C["bg_mid"]).pack(expand=True)

    def _contact_row(self, contact):
        active = contact["id"] == self._active_contact
        row = tk.Frame(self._contact_panel,
                       bg=C["teal_900"] if active else C["bg_dark"],
                       cursor="hand2")
        row.pack(fill="x")
        inner = tk.Frame(row, bg=row.cget("bg")); inner.pack(fill="x", padx=16, pady=12)

        initials = "".join(w[0] for w in contact["name"].split()[:2]).upper()
        tk.Label(inner, text=initials, width=4, height=2,
                 bg=C["teal_700"], fg=C["text_primary"],
                 font=("Helvetica", FS["small"], "bold")).pack(side="left", padx=(0, 10))

        col = tk.Frame(inner, bg=inner.cget("bg")); col.pack(side="left", fill="x", expand=True)
        label(col, contact["name"], size="body", bold=True,
              bg=inner.cget("bg")).pack(anchor="w")
        role_txt = "Client" if contact["role"] == "client" else "Therapist"
        label(col, role_txt, size="small", color=C["text_secondary"],
              bg=inner.cget("bg")).pack(anchor="w")

        def _click(_=None, cid=contact["id"]):
            self._active_contact = cid
            for w in self._contact_panel.winfo_children(): w.destroy()
            contacts = self.app.db.get_conversations_for_user(self.user["id"])
            all_ids = [c["id"] for c in contacts]
            if cid not in all_ids:
                u = self.app.db.get_user_by_id(cid)
                if u: contacts.append(u)
            for c in contacts:
                self._contact_row(c)
            for w in self._thread_panel.winfo_children(): w.destroy()
            self._render_thread(cid)

        row.bind("<Button-1>", _click)
        inner.bind("<Button-1>", _click)
        for w in inner.winfo_children():
            w.bind("<Button-1>", _click)

    def _render_thread(self, contact_id):
        contact = self.app.db.get_user_by_id(contact_id)
        if not contact:
            label(self._thread_panel, "Contact not found.",
                  bg=C["bg_mid"]).pack(expand=True)
            return

        # header
        th_hdr = tk.Frame(self._thread_panel, bg=C["bg_dark"], height=60)
        th_hdr.pack(fill="x"); th_hdr.pack_propagate(False)
        hinner = tk.Frame(th_hdr, bg=C["bg_dark"]); hinner.pack(fill="both", padx=20, pady=10)
        initials = "".join(w[0] for w in contact["name"].split()[:2]).upper()
        tk.Label(hinner, text=initials, width=4, height=2, bg=C["teal_700"],
                 fg=C["text_primary"], font=("Helvetica", FS["small"], "bold")).pack(side="left", padx=(0,10))
        label(hinner, contact["name"], size="body", bold=True, bg=C["bg_dark"]).pack(side="left")

        # messages body (scrollable)
        canvas = tk.Canvas(self._thread_panel, bg=C["slate_900"], highlightthickness=0)
        vsb = ttk.Scrollbar(self._thread_panel, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        msg_frame = tk.Frame(canvas, bg=C["slate_900"])
        win = canvas.create_window((0,0), window=msg_frame, anchor="nw")
        msg_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        convo = self.app.db.get_conversation(self.user["id"], contact_id)
        self.app.db.mark_messages_read(contact_id, self.user["id"])

        pad = tk.Frame(msg_frame, bg=C["slate_900"]); pad.pack(fill="both", expand=True, padx=20, pady=16)
        for m in convo:
            outgoing = m["sender_id"] == self.user["id"]
            row = tk.Frame(pad, bg=C["slate_900"]); row.pack(fill="x", pady=4)
            bubble = tk.Frame(row, bg=C["teal_600"] if outgoing else C["bg_card"])
            bubble.pack(side="right" if outgoing else "left", padx=4)
            tk.Label(bubble, text=m["body"], bg=bubble.cget("bg"),
                fg=C["text_primary"], font=("Helvetica", FS["body"]),
                wraplength=400, justify="left", padx=14, pady=10).pack()
            tk.Label(row, text=_fmt_ts(m["sent_at"]), bg=C["slate_900"],
                fg=C["text_secondary"], font=("Helvetica", FS["small"])).pack(
                side="right" if outgoing else "left", padx=8)

        canvas.after(50, lambda: canvas.yview_moveto(1.0))

        # input bar
        input_bar = tk.Frame(self._thread_panel, bg=C["bg_dark"], height=60)
        input_bar.pack(fill="x"); input_bar.pack_propagate(False)
        iinner = tk.Frame(input_bar, bg=C["bg_dark"]); iinner.pack(fill="both", padx=16, pady=10)

        msg_var = tk.StringVar()
        entry = ttk.Entry(iinner, textvariable=msg_var, font=("Helvetica", FS["body"]))
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        entry.focus_set()

        def _send(_=None):
            text = msg_var.get().strip()
            if not text: return
            self.app.db.send_message(self.user["id"], contact_id, text)
            msg_var.set("")
            for w in self._thread_panel.winfo_children(): w.destroy()
            self._render_thread(contact_id)

        entry.bind("<Return>", _send)
        button(iinner, "Send →", _send, style="primary").pack(side="left", ipady=4)
