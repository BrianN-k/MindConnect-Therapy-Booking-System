"""
Email notification service.
=============================

Handles composing and sending appointment confirmations, reminders, and
payment receipts.

Configuration
-------------
Set these environment variables to send **real** emails via SMTP:

    MINDCONNECT_SMTP_HOST      e.g. smtp.gmail.com
    MINDCONNECT_SMTP_PORT      e.g. 587
    MINDCONNECT_SMTP_USER      your sending address
    MINDCONNECT_SMTP_PASSWORD  an app password (NOT your normal password)
    MINDCONNECT_FROM_EMAIL     defaults to MINDCONNECT_SMTP_USER if unset

If these are not set, the service runs in **demo mode**: every email is
still composed and logged into the `email_outbox` table (visible in the
Admin dashboard's "Email Notifications" tab) but is not actually
transmitted over the network. This lets the full notification pipeline be
demonstrated even without configuring a real mailbox.
"""

import os
import smtplib
import ssl
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def _smtp_config():
    return {
        "host":     os.environ.get("MINDCONNECT_SMTP_HOST", ""),
        "port":     int(os.environ.get("MINDCONNECT_SMTP_PORT", "587") or 587),
        "user":     os.environ.get("MINDCONNECT_SMTP_USER", ""),
        "password": os.environ.get("MINDCONNECT_SMTP_PASSWORD", ""),
        "from":     os.environ.get("MINDCONNECT_FROM_EMAIL",
                                    os.environ.get("MINDCONNECT_SMTP_USER", "no-reply@mindconnect.ke")),
    }


def is_configured() -> bool:
    cfg = _smtp_config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def _fmt_date(d):
    try: return datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %B %Y")
    except Exception: return d or ""


def _fmt_time(t):
    try:
        h, m = t.split(":"); h = int(h)
        return f"{h if h<=12 else h-12}:{m} {'AM' if h<12 else 'PM'}"
    except Exception:
        return t or ""


# ════════════════════════════════════════════════════
# LOW-LEVEL SEND
# ════════════════════════════════════════════════════
def send_now(db, to_email, subject, body, related_appointment=None) -> bool:
    """
    Queue + attempt to send an email. Always writes a row to email_outbox
    (so it shows up in the Admin > Email Notifications log), then either
    sends for real (if SMTP is configured) or marks it demo_logged.
    Returns True if it was sent or demo-logged successfully, False on
    a real SMTP failure.
    """
    eid = db.queue_email(to_email, subject, body, related_appointment)

    if not is_configured():
        db.mark_email_status(eid, "demo_logged")
        print(f"[EMAIL - DEMO MODE] To: {to_email} | Subject: {subject}")
        return True

    cfg = _smtp_config()
    try:
        msg = MIMEMultipart()
        msg["From"] = cfg["from"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
            server.starttls(context=context)
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from"], [to_email], msg.as_string())

        db.mark_email_status(eid, "sent")
        return True
    except Exception as e:
        print(f"[EMAIL - SEND FAILED] {e}")
        db.mark_email_status(eid, "failed")
        return False


def send_async(db, to_email, subject, body, related_appointment=None):
    """Fire-and-forget version so the UI never blocks on network I/O."""
    t = threading.Thread(
        target=send_now,
        args=(db, to_email, subject, body, related_appointment),
        daemon=True
    )
    t.start()
    return t


# ════════════════════════════════════════════════════
# MESSAGE COMPOSERS
# ════════════════════════════════════════════════════
def compose_booking_confirmation(client_name, therapist_name, date_, time_, type_, amount):
    subject = f"Appointment confirmed with {therapist_name}"
    body = (
        f"Hi {client_name},\n\n"
        f"Your appointment has been confirmed.\n\n"
        f"  Therapist : {therapist_name}\n"
        f"  Date      : {_fmt_date(date_)}\n"
        f"  Time      : {_fmt_time(time_)}\n"
        f"  Type      : {'Online / Video' if type_ == 'online' else 'In-person'}\n"
        f"  Amount    : KSh {amount:,}\n\n"
        f"You will receive reminders 24 hours and 1 hour before your session.\n\n"
        f"— MindConnect"
    )
    return subject, body


def compose_reminder(client_name, therapist_name, date_, time_, hours_before):
    subject = f"Reminder: your session with {therapist_name} is coming up"
    when = "tomorrow" if hours_before >= 24 else "in 1 hour"
    body = (
        f"Hi {client_name},\n\n"
        f"This is a reminder that your therapy session with {therapist_name} "
        f"is {when}.\n\n"
        f"  Date : {_fmt_date(date_)}\n"
        f"  Time : {_fmt_time(time_)}\n\n"
        f"If you need to reschedule or cancel, please do so from your "
        f"MindConnect dashboard as soon as possible so another client can "
        f"take the slot if needed.\n\n"
        f"— MindConnect"
    )
    return subject, body


def compose_payment_receipt(client_name, therapist_name, amount, method, transaction_ref, date_, time_):
    subject = f"Payment receipt — KSh {amount:,}"
    body = (
        f"Hi {client_name},\n\n"
        f"We've received your payment for your upcoming session.\n\n"
        f"  Therapist        : {therapist_name}\n"
        f"  Session date     : {_fmt_date(date_)}\n"
        f"  Session time     : {_fmt_time(time_)}\n"
        f"  Amount paid      : KSh {amount:,}\n"
        f"  Payment method   : {method.upper()}\n"
        f"  Transaction ref  : {transaction_ref}\n\n"
        f"Thank you for using MindConnect.\n\n"
        f"— MindConnect"
    )
    return subject, body


def compose_new_booking_alert_for_therapist(therapist_name, client_name, date_, time_, type_):
    subject = f"New booking from {client_name}"
    body = (
        f"Hi {therapist_name},\n\n"
        f"You have a new appointment booking.\n\n"
        f"  Client : {client_name}\n"
        f"  Date   : {_fmt_date(date_)}\n"
        f"  Time   : {_fmt_time(time_)}\n"
        f"  Type   : {'Online / Video' if type_ == 'online' else 'In-person'}\n\n"
        f"Log in to your MindConnect dashboard to view full details.\n\n"
        f"— MindConnect"
    )
    return subject, body


def compose_waitlist_opening(client_name, therapist_name):
    subject = f"A slot opened up with {therapist_name}!"
    body = (
        f"Hi {client_name},\n\n"
        f"Good news — a slot with {therapist_name} that you were waitlisted "
        f"for has just become available.\n\n"
        f"Log in to MindConnect now to book it before someone else does.\n\n"
        f"— MindConnect"
    )
    return subject, body
