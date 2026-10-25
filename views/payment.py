"""
Payment view — choose a method (M-Pesa / Card / Insurance / Pay at session),
simulate processing, then create the appointment + payment record and fire
off confirmation / receipt emails.

No real payment gateway is integrated (this is a student project running
locally); the "processing" step is simulated with a short delay so the UX
matches a real M-Pesa STK-push / card charge flow.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import random

from views.styles import C, FS, label, button, card_frame, nav_bar, entry
from services import email_service

INSURANCE_PROVIDERS = ["NHIF", "AAR", "Jubilee", "Britam", "Madison", "CIC", "Other"]


def _fmt_date(d):
    try: return datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %B %Y")
    except Exception: return d or ""

def _fmt_time(t):
    try:
        h, m = t.split(":"); h = int(h)
        return f"{h if h<=12 else h-12}:{m} {'AM' if h<12 else 'PM'}"
    except Exception:
        return t or ""


class PaymentView(tk.Frame):
    def __init__(self, parent, app, booking):
        super().__init__(parent, bg=C["bg_mid"])
        self.app = app
        self.booking = booking          # dict: client_id, therapist_id, date, time, type, notes, amount
        self.t = app.db.get_therapist_by_id(booking["therapist_id"])
        self._method = tk.StringVar(value="mpesa")
        self._build()

    # ════════════════════════════════════════════════
    def _build(self):
        nav_bar(self, self.app, show_back=True,
                back_cmd=lambda: self.app.show_book_appointment(self.booking["therapist_id"]))

        hdr = tk.Frame(self, bg=C["bg_dark"]); hdr.pack(fill="x")
        label(hdr, "Payment", size="h2", bold=True, bg=C["bg_dark"]).pack(
            padx=24, pady=(20, 4), anchor="w")
        label(hdr, f"Complete payment to confirm your session with {self.t['name']}",
              size="body", color=C["text_secondary"],
              bg=C["bg_dark"]).pack(padx=24, pady=(0, 16), anchor="w")

        canvas = tk.Canvas(self, bg=C["bg_mid"], highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=C["bg_mid"])
        win = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        cols = tk.Frame(body, bg=C["bg_mid"]); cols.pack(fill="both", expand=True, padx=24, pady=24)
        left = tk.Frame(cols, bg=C["bg_mid"]); left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(cols, bg=C["bg_mid"], width=320); right.pack(side="left", fill="y")
        right.pack_propagate(False)

        self._build_methods(left)
        self._build_order_summary(right)

    # ─── payment method selector ─────────────────────
    def _build_methods(self, parent):
        card = card_frame(parent); card.pack(fill="x", pady=(0, 16))
        label(card, "Choose payment method", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 10))

        methods_row = tk.Frame(card, bg=C["bg_card"]); methods_row.pack(fill="x", padx=16, pady=(0, 16))
        self._method_btns = {}
        for val, txt, icon in [
            ("mpesa",     "M-Pesa",           "📱"),
            ("card",      "Card",             "💳"),
            ("insurance", "Insurance",        "🏥"),
            ("cash",      "Pay at session",   "🤝"),
        ]:
            btn = tk.Button(methods_row, text=f"{icon}\n{txt}",
                command=lambda v=val: self._switch_method(v),
                bg=C["teal_600"] if val == "mpesa" else C["bg_dark"],
                fg=C["text_primary"], relief="flat", cursor="hand2",
                font=("Helvetica", FS["small"]), padx=18, pady=12, justify="center")
            btn.pack(side="left", padx=(0, 10))
            self._method_btns[val] = btn

        # Dynamic form area
        self._form_area = tk.Frame(card, bg=C["bg_card"])
        self._form_area.pack(fill="x", padx=16, pady=(0, 16))
        self._render_form("mpesa")

        self._err_lbl = label(card, "", size="small", color=C["red_400"], bg=C["bg_card"])
        self._err_lbl.pack(anchor="w", padx=16, pady=(0, 4))

        self._pay_btn = button(card, f"Pay KSh {self.booking['amount']:,} →",
                               self._process_payment, style="primary")
        self._pay_btn.pack(fill="x", padx=16, pady=(4, 16), ipady=8)

        # Security note
        note = card_frame(parent); note.pack(fill="x")
        label(note, "🔒  Secure checkout", size="small", bold=True,
              color=C["teal_300"], bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(12, 4))
        label(note,
              "Your payment details are processed securely and are never shared "
              "with your therapist. MindConnect only stores a transaction "
              "reference for your records.",
              size="small", color=C["text_secondary"], bg=C["bg_card"],
              wraplength=460, justify="left").pack(anchor="w", padx=16, pady=(0, 14))

    def _switch_method(self, method):
        self._method.set(method)
        for val, btn in self._method_btns.items():
            btn.config(bg=C["teal_600"] if val == method else C["bg_dark"])
        self._render_form(method)
        self._err_lbl.config(text="")

    def _render_form(self, method):
        for w in self._form_area.winfo_children():
            w.destroy()

        if method == "mpesa":
            label(self._form_area, "M-Pesa phone number", size="label",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(4, 2))
            self._mpesa_entry, self._mpesa_var = entry(
                self._form_area, placeholder="+254 7XX XXX XXX", width=40)
            self._mpesa_entry.pack(fill="x", ipady=5)
            label(self._form_area,
                  "You'll receive an STK push prompt on your phone to complete payment.",
                  size="small", color=C["text_secondary"],
                  bg=C["bg_card"]).pack(anchor="w", pady=(6, 0))

        elif method == "card":
            label(self._form_area, "Card number", size="label",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(4, 2))
            self._card_entry, self._card_var = entry(
                self._form_area, placeholder="4242 4242 4242 4242", width=40)
            self._card_entry.pack(fill="x", ipady=5, pady=(0, 10))

            row = tk.Frame(self._form_area, bg=C["bg_card"]); row.pack(fill="x")
            col1 = tk.Frame(row, bg=C["bg_card"]); col1.pack(side="left", expand=True, fill="x", padx=(0, 8))
            col2 = tk.Frame(row, bg=C["bg_card"]); col2.pack(side="left", expand=True, fill="x")
            label(col1, "Expiry", size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w")
            self._exp_entry, self._exp_var = entry(col1, placeholder="MM/YY")
            self._exp_entry.pack(fill="x", ipady=5, pady=(2, 0))
            label(col2, "CVV", size="label", color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w")
            self._cvv_entry, self._cvv_var = entry(col2, placeholder="123", show="•")
            self._cvv_entry.pack(fill="x", ipady=5, pady=(2, 0))

        elif method == "insurance":
            label(self._form_area, "Insurance provider", size="label",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(4, 2))
            self._ins_var = tk.StringVar(value=INSURANCE_PROVIDERS[0])
            cb = ttk.Combobox(self._form_area, textvariable=self._ins_var,
                              values=INSURANCE_PROVIDERS, state="readonly", width=38)
            cb.pack(fill="x", ipady=4)
            label(self._form_area, "Member/policy number", size="label",
                  color=C["text_secondary"], bg=C["bg_card"]).pack(anchor="w", pady=(10, 2))
            self._policy_entry, self._policy_var = entry(
                self._form_area, placeholder="e.g. NHIF-0012345", width=40)
            self._policy_entry.pack(fill="x", ipady=5)
            label(self._form_area,
                  "We'll verify your cover and bill your insurer directly. "
                  "Your session is confirmed immediately; verification "
                  "happens in the background.",
                  size="small", color=C["text_secondary"], bg=C["bg_card"],
                  wraplength=440, justify="left").pack(anchor="w", pady=(8, 0))

        elif method == "cash":
            label(self._form_area,
                  "You've chosen to pay in person at the time of your session. "
                  "Your appointment will be confirmed now — please bring "
                  f"KSh {self.booking['amount']:,} (cash or M-Pesa) to your appointment.",
                  size="body", color=C["text_secondary"], bg=C["bg_card"],
                  wraplength=460, justify="left").pack(anchor="w", pady=(4, 0))

    # ─── order summary sidebar ────────────────────────
    def _build_order_summary(self, parent):
        card = card_frame(parent); card.pack(fill="x")
        label(card, "Order summary", size="h4", bold=True,
              bg=C["bg_card"]).pack(anchor="w", padx=16, pady=(14, 10))

        rows = [
            ("Therapist", self.t["name"]),
            ("Date",      _fmt_date(self.booking["date"])),
            ("Time",      _fmt_time(self.booking["time"])),
            ("Type",      "🖥 Online" if self.booking["type"] == "online" else "🏢 In-person"),
        ]
        for k, v in rows:
            r = tk.Frame(card, bg=C["bg_card"]); r.pack(fill="x", padx=16, pady=3)
            label(r, k, size="small", color=C["text_secondary"], bg=C["bg_card"]).pack(side="left")
            label(r, v, size="small", bold=True, bg=C["bg_card"]).pack(side="right")

        tk.Frame(card, bg=C["slate_900"], height=1).pack(fill="x", padx=16, pady=10)

        total_row = tk.Frame(card, bg=C["bg_card"]); total_row.pack(fill="x", padx=16, pady=(0, 16))
        label(total_row, "Total due", size="body", bold=True, bg=C["bg_card"]).pack(side="left")
        label(total_row, f"KSh {self.booking['amount']:,}", size="h4", bold=True,
              color=C["teal_300"], bg=C["bg_card"]).pack(side="right")

    # ════════════════════════════════════════════════
    # PROCESS PAYMENT
    # ════════════════════════════════════════════════
    def _process_payment(self):
        method = self._method.get()

        # ── validation per method ────────────────────
        if method == "mpesa":
            phone = self._mpesa_var.get().strip()
            if not phone or phone == "+254 7XX XXX XXX" or len(phone) < 10:
                self._err_lbl.config(text="Please enter a valid M-Pesa phone number."); return
        elif method == "card":
            num = self._card_var.get().strip()
            exp = self._exp_var.get().strip()
            cvv = self._cvv_var.get().strip()
            if not num or num == "4242 4242 4242 4242" or len(num.replace(" ", "")) < 12:
                self._err_lbl.config(text="Please enter a valid card number."); return
            if not exp or exp == "MM/YY":
                self._err_lbl.config(text="Please enter the card expiry."); return
            if not cvv or cvv == "123" or len(cvv) < 3:
                self._err_lbl.config(text="Please enter the CVV."); return
        elif method == "insurance":
            policy = self._policy_var.get().strip()
            if not policy or policy == "e.g. NHIF-0012345":
                self._err_lbl.config(text="Please enter your policy/member number."); return

        self._err_lbl.config(text="")
        self._pay_btn.config(state="disabled", text="Processing payment…")
        self.update_idletasks()

        # Simulate network/gateway delay, then finalize
        self.after(900, lambda: self._finalize(method))

    def _finalize(self, method):
        b = self.booking

        # 1) Create the appointment now that payment is authorised
        aid, err = self.app.db.create_appointment(
            client_id=b["client_id"], therapist_id=b["therapist_id"],
            date_=b["date"], time_=b["time"], type_=b["type"],
            notes=b["notes"], amount=b["amount"]
        )
        if err:
            self._pay_btn.config(state="normal", text=f"Pay KSh {b['amount']:,} →")
            self._err_lbl.config(text=err)
            return

        # 2) Record the payment
        transaction_ref = f"MC{random.randint(100000, 999999)}"
        payment_status = "completed" if method in ("mpesa", "card") else "pending"
        insurance_provider = self._ins_var.get() if method == "insurance" else ""

        self.app.db.create_payment(
            appointment_id=aid, client_id=b["client_id"], therapist_id=b["therapist_id"],
            amount=b["amount"], method=method, status=payment_status,
            transaction_ref=transaction_ref, insurance_provider=insurance_provider
        )

        # 3) Fire off notification emails (async — never blocks the UI)
        client = self.app.db.get_user_by_id(b["client_id"])
        therapist_user_email = self.t.get("email", "")

        subj, body = email_service.compose_booking_confirmation(
            client["name"], self.t["name"], b["date"], b["time"], b["type"], b["amount"])
        email_service.send_async(self.app.db, client["email"], subj, body, related_appointment=aid)

        if payment_status == "completed":
            subj2, body2 = email_service.compose_payment_receipt(
                client["name"], self.t["name"], b["amount"], method, transaction_ref,
                b["date"], b["time"])
            email_service.send_async(self.app.db, client["email"], subj2, body2, related_appointment=aid)

        if therapist_user_email:
            subj3, body3 = email_service.compose_new_booking_alert_for_therapist(
                self.t["name"], client["name"], b["date"], b["time"], b["type"])
            email_service.send_async(self.app.db, therapist_user_email, subj3, body3, related_appointment=aid)

        # 4) Show success and route to dashboard
        method_label = {"mpesa": "M-Pesa", "card": "Card", "insurance": "Insurance", "cash": "Pay at session"}[method]
        extra = ""
        if method == "insurance":
            extra = "\n\nYour insurance claim will be verified with your provider; you're all set for your session."
        elif method == "cash":
            extra = f"\n\nPlease bring KSh {b['amount']:,} to your session."

        messagebox.showinfo("Payment successful ✅",
            f"Your session with {self.t['name']} is confirmed!\n\n"
            f"Payment method : {method_label}\n"
            f"Transaction ref: {transaction_ref}\n"
            f"Amount         : KSh {b['amount']:,}\n\n"
            "📧  A confirmation email and receipt have been sent.\n"
            "🔔  You'll receive reminders 24 hours and 1 hour before your session."
            f"{extra}")
        self.app.show_client_dashboard()
