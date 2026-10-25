# MindConnect
### Mental Health & Therapist Booking System

A desktop application built with **Python + Tkinter + SQLite**, .
 
| **Stack**      | Python 3.10+, Tkinter, SQLite (dev) / PostgreSQL-ready (prod) |

---

## 1. What this system does

MindConnect lets **clients** search for licensed **therapists** by speciality,
location, price, language and insurance; view real-time availability; book,
pay for, reschedule or cancel appointments; join a waitlist when a therapist
is fully booked; and message their therapist securely.

**Therapists** manage their own profile, weekly availability, incoming
bookings (accept/decline), client list, and earnings — all from their own
dashboard, including revenue and payment-method charts.

**Administrators** get a system-wide view: total users, appointment demand
per therapist (bar chart), appointment status breakdown (pie chart),
platform revenue by month (line chart), every payment transaction, and a
live log of every notification email sent.

This directly implements the functional requirements from Chapter 3 of the
accompanying System Requirements Specification (client/therapist
registration, real-time scheduling with no double-booking, **secure
payment/insurance processing**, automated email reminders, waitlist
automation, an admin dashboard **with demand analytics**, secure messaging,
and role-based access).

### Payments
Booking flow now runs: *pick a slot → **Proceed to payment** → choose
M-Pesa / Card / Insurance / Pay-at-session → the appointment and a payment
record are only created once payment is authorised*. Every payment is
logged with a transaction reference and visible in the Client "Payments"
tab, the Therapist "Earnings" tab, and the Admin "Payments" tab.

### Charts
Built with `matplotlib` embedded directly into the Tkinter windows:
- **Admin → Overview**: appointment demand per therapist (bar), appointment
  status breakdown (pie), platform revenue by month (line)
- **Admin → Payments**: payments by method (pie)
- **Therapist → Earnings**: revenue by month (line), payments by method (pie)

If `matplotlib` isn't installed, these panels show a friendly
"install matplotlib" placeholder instead of crashing — the rest of the app
is unaffected.

### Email notifications
Real emails are composed and sent for: booking confirmation, payment
receipt, new-booking alert (to the therapist), appointment reminders
(24 h and 1 h before, sent automatically by a background scheduler thread),
and waitlist-slot-opened alerts. See §6 below for SMTP configuration —
without it, the system runs in **demo mode** and every email is still
logged and viewable under **Admin → Email Notifications**.

### User management (Admin / front desk)
Under **Admin → Clients** and **Admin → Therapists**:
- **Search** — a search box filters the list live (by name, email, phone
  for clients; name, email, title, or location for therapists), combined
  with the Active/Archived tab so front-desk staff can quickly find any
  account to act on
- **Add Client** / **Add Therapist** — opens a form that creates a login
  account (and, for therapists, a public profile) immediately usable to
  sign in
- **Edit** — opens a pre-filled form to correct or update a client's or
  therapist's details (name, email, phone, and — for therapists —
  title, specialities, languages, price, location, insurance, free-session
  and online/in-person flags). Changes take effect immediately and are
  visible to clients right away. Email changes are checked for uniqueness
  against every other account
- **Archive** — soft-disables an account: it disappears from active lists
  and client-facing search, and can no longer sign in, but all of its
  historical appointments, payments, and messages are preserved. An
  **Active / Archived** tab toggle lets the admin switch between views, and
  archived accounts can be **Restored** at any time
- **Delete** (therapists only) — permanently removes a therapist's account
  and profile. To protect appointment/payment history, deletion is
  **blocked** if the therapist has any appointment on record — archive
  instead in that case. Clients are never hard-deleted, only archived, so
  their booking history always stays intact for the therapists who saw them

### Rescheduling (Client)
From **My Appointments**, any confirmed or pending session that hasn't
started yet shows a **Reschedule** button alongside Cancel. It opens a
day/time picker scoped to that same therapist's real availability —
already-booked slots are disabled — and on confirmation the appointment
moves to the new slot in place (no new booking or duplicate payment is
created), stale reminders are cleared and fresh 24 h/1 h reminders are
scheduled for the new time, and the therapist is emailed a
reschedule notice. Sessions that have already started, or that are
completed/cancelled, cannot be rescheduled.

---

## 2. Requirements

- **Python 3.10 or newer**
- **Tkinter** — ships with the standard Python installer on Windows and
  macOS. On Linux it is a separate package:

  ```bash
  # Ubuntu / Debian
  sudo apt install python3-tk

  # Fedora
  sudo dnf install python3-tkinter

  # Arch
  sudo pacman -S tk
  ```

- **matplotlib** — powers the charts in the Admin and Therapist dashboards:

  ```bash
  pip install -r requirements.txt
  ```

  If you skip this step the app still runs fine — chart panels simply show
  a placeholder asking you to install matplotlib.

No other third-party packages are required for the default SQLite
configuration — the database file `db/mindconnect.db` is created
automatically on first run and seeded with demo data.

---

## 3. Running the application

```bash
cd mindconnect
python main.py
```

A 1200×750 window will open, starting on the **Sign In** screen.

### Demo accounts (seeded automatically)

| Role       | Email                     | Password  |
|------------|----------------------------|-----------|
| Client     | amina@example.com          | pass123   |
| Client     | james@example.com          | pass123   |
| Client     | grace@example.com          | pass123   |
| Therapist  | sarah@example.com          | pass123   |
| Therapist  | kevin@example.com          | pass123   |
| Therapist  | fatuma@example.com         | pass123   |
| Therapist  | brian@example.com          | pass123   |
| Admin      | admin@mindconnect.ke       | admin123  |

The login screen has clickable shortcuts for the first three of these.

To start completely fresh, delete `db/mindconnect.db` before running —
it will be recreated and reseeded automatically.

---

## 4. Project structure

```
mindconnect/
├── main.py                      # App entry point — single-window frame switcher
├── requirements.txt
├── README.md
├── db/
│   ├── database.py               # All SQL — schema + CRUD + search + stats
│   ├── seed.py                   # Demo data (users, therapists, appointments, payments…)
│   └── mindconnect.db            # Created automatically on first run
├── services/
│   ├── email_service.py          # SMTP sending + demo-mode fallback + message composers
│   └── reminder_scheduler.py     # Background thread that sends due reminder emails
└── views/
    ├── styles.py                  # Centralised colour palette + widget factories
    ├── charts.py                  # matplotlib chart embedding (bar / line / pie)
    ├── login.py                   # Sign-in screen
    ├── register.py                # Client / Therapist sign-up
    ├── find_therapist.py          # Search + filter directory
    ├── therapist_profile.py       # Public therapist profile page
    ├── book_appointment.py        # Day → slot → session type → notes → payment
    ├── payment.py                 # M-Pesa / Card / Insurance / Cash checkout
    ├── client_dashboard.py        # Overview / Appointments / Payments / Waitlist / Profile
    ├── therapist_dashboard.py     # Overview / Schedule / Clients / Earnings / Availability / Profile
    ├── admin_dashboard.py         # Overview (charts) / Appointments / Payments / Therapists / Clients / Waitlist / Emails
    └── messages.py                # Secure client ⇄ therapist messaging
```

---

## 5. Architecture

**3-tier design**, matching Chapter 3.8 of the SRS:

| Tier | Implementation |
|---|---|
| Presentation | Tkinter widgets (`views/`), styled via a single `styles.py` theme module |
| Application  | View classes hold all business logic (validation, booking rules, filtering) |
| Data         | `db/database.py` — a single `Database` class wrapping SQLite; every method maps 1:1 to a future PostgreSQL query, so swapping the connection layer for production is a contained change |

**Key business rules implemented:**
- No double-booking — `is_slot_booked()` is checked before every appointment insert
- Payment-first booking — the appointment record is only created after the
  simulated payment gateway authorises the transaction (`views/payment.py`)
- Cancelling an appointment automatically checks the waitlist, marks the
  next person as notified, and **emails them** that a slot opened up
  (`_notify_waitlist_for_appointment` + `email_service.compose_waitlist_opening`)
- Every confirmed booking schedules two reminder rows (24 h and 1 h before
  the session) in the `reminders` table; a background daemon thread
  (`services/reminder_scheduler.py`) polls every 30 seconds and emails any
  that are due
- Passwords are SHA-256 hashed before storage (see `db/database.py:_hash`)

---

## 6. Configuring real email delivery (optional)

By default MindConnect runs in **demo mode**: every notification email is
composed and logged to the `email_outbox` table (viewable under
**Admin → Email Notifications**) but not actually transmitted. This lets you
demo the full notification pipeline — booking confirmations, payment
receipts, 24 h/1 h reminders, waitlist alerts — without needing a real
mailbox.

To send **real** emails, set these environment variables before running
`python main.py`:

```bash
export MINDCONNECT_SMTP_HOST=smtp.gmail.com
export MINDCONNECT_SMTP_PORT=587
export MINDCONNECT_SMTP_USER=youraddress@gmail.com
export MINDCONNECT_SMTP_PASSWORD=your16digitapppassword
export MINDCONNECT_FROM_EMAIL=youraddress@gmail.com   # optional, defaults to SMTP_USER

python main.py
```

For Gmail, `MINDCONNECT_SMTP_PASSWORD` must be an
[App Password](https://myaccount.google.com/apppasswords), not your normal
account password (Google blocks plain-password SMTP login by default).

Once these are set, `services/email_service.is_configured()` returns
`True` and every email is sent for real over TLS — the Admin dashboard
banner will confirm this and outbox rows will show `status = sent` instead
of `demo_logged`.

## 7. Switching to PostgreSQL for production

`db/database.py` uses only standard SQL (no SQLite-only syntax except the
`sqlite3.Row` row factory). To move to PostgreSQL:

1. `pip install psycopg2-binary`
2. Replace the `sqlite3.connect(...)` call in `Database.__init__` with a
   `psycopg2.connect(...)` call using your connection string
3. Replace `cursor.executescript(...)` in `_create_tables()` with individual
   `cursor.execute()` calls (psycopg2 does not support `executescript`)
4. Replace `?` placeholders with `%s` throughout

Everything else — every view, every business rule — stays unchanged, since
they only ever call methods on the `Database` object.

---

## 8. Known limitations / next steps

- Payments are simulated (M-Pesa STK-push and card charges are not wired to
  a real gateway — Safaricom Daraja API / Stripe integration would replace
  the `_finalize()` simulation in `views/payment.py` with a real API call)
- SMS reminders are composed and logged the same way as emails but are not
  sent over a real SMS gateway (e.g. Africa's Talking) — only the "email"
  reminder type actually transmits when SMTP is configured; the "sms" type
  reminder is demo-logged the same way emails are in demo mode
- The UI was developed and logic-tested in a headless sandbox using a
  custom Tkinter test shim (no real display was available in that
  environment). All navigation, filtering, booking, payment (all 4
  methods), cancellation + waitlist email notification, the reminder
  scheduler, messaging, and profile-editing flows were exercised
  programmatically and confirmed bug-free, but a final visual/spacing pass
  on a real screen is recommended before your final submission/demo.
- Chart rendering (matplotlib + Tkinter's `TkAgg` backend) could not be
  visually verified in the same sandbox for the same reason; the data-prep
  logic behind every chart was tested directly against the database and is
  correct, and the module degrades gracefully to a text placeholder if
  matplotlib isn't installed, but do glance at the actual charts once
  running locally.

---

## 9. Credits

Developed by **Kipkemboi Brian Kipkosgei** 
