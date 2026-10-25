"""
Database layer — SQLite for development, PostgreSQL-ready for production.
All SQL is standard; swap the connection string in __init__ for PostgreSQL.
"""

import sqlite3, os, hashlib, uuid
from datetime import datetime, date


DB_PATH = os.path.join(os.path.dirname(__file__), "mindconnect.db")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row          # rows as dict-like objects
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._migrate()

    # ════════════════════════════════════════════════
    # SCHEMA
    # ════════════════════════════════════════════════
    def _create_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL CHECK(role IN ('client','therapist','admin')),
            phone       TEXT,
            is_archived INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS therapists (
            id              TEXT PRIMARY KEY,
            user_id         TEXT REFERENCES users(id),
            title           TEXT,
            specialities    TEXT,          -- comma-separated
            location        TEXT,
            languages       TEXT,          -- comma-separated
            price           INTEGER DEFAULT 0,
            free_available  INTEGER DEFAULT 0,
            online          INTEGER DEFAULT 1,
            in_person       INTEGER DEFAULT 1,
            rating          REAL DEFAULT 0,
            review_count    INTEGER DEFAULT 0,
            insurance       TEXT,          -- comma-separated
            about           TEXT,
            experience      TEXT,
            education       TEXT
        );

        CREATE TABLE IF NOT EXISTS availability (
            id            TEXT PRIMARY KEY,
            therapist_id  TEXT REFERENCES therapists(id),
            day_of_week   TEXT NOT NULL,
            time_slot     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id            TEXT PRIMARY KEY,
            client_id     TEXT REFERENCES users(id),
            therapist_id  TEXT REFERENCES therapists(id),
            date          TEXT NOT NULL,
            time          TEXT NOT NULL,
            type          TEXT CHECK(type IN ('online','in-person')),
            status        TEXT DEFAULT 'confirmed'
                          CHECK(status IN ('confirmed','pending','completed','cancelled')),
            notes         TEXT,
            amount        INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          TEXT PRIMARY KEY,
            sender_id   TEXT REFERENCES users(id),
            receiver_id TEXT REFERENCES users(id),
            body        TEXT NOT NULL,
            sent_at     TEXT DEFAULT CURRENT_TIMESTAMP,
            is_read     INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS waitlist (
            id            TEXT PRIMARY KEY,
            client_id     TEXT REFERENCES users(id),
            therapist_id  TEXT REFERENCES therapists(id),
            added_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            notified      INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id              TEXT PRIMARY KEY,
            appointment_id  TEXT REFERENCES appointments(id),
            remind_at       TEXT NOT NULL,
            type            TEXT,          -- email | sms
            sent            INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS payments (
            id              TEXT PRIMARY KEY,
            appointment_id  TEXT REFERENCES appointments(id),
            client_id       TEXT REFERENCES users(id),
            therapist_id    TEXT REFERENCES therapists(id),
            amount          INTEGER NOT NULL,
            method          TEXT NOT NULL,      -- mpesa | card | insurance | cash
            status          TEXT DEFAULT 'pending'
                            CHECK(status IN ('pending','completed','failed','refunded')),
            transaction_ref TEXT,
            insurance_provider TEXT,
            paid_at         TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_outbox (
            id                  TEXT PRIMARY KEY,
            to_email            TEXT NOT NULL,
            subject             TEXT NOT NULL,
            body                TEXT NOT NULL,
            related_appointment TEXT,
            status              TEXT DEFAULT 'pending'
                                CHECK(status IN ('pending','sent','failed','demo_logged')),
            created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            sent_at             TEXT
        );
        """)
        self.conn.commit()

    def _migrate(self):
        """Safety-net for databases created before a schema change (e.g.
        upgrading an existing mindconnect.db that predates is_archived)."""
        try:
            self.conn.execute("ALTER TABLE users ADD COLUMN is_archived INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    # ════════════════════════════════════════════════
    # USER OPERATIONS
    # ════════════════════════════════════════════════
    def create_user(self, name, email, password, role, phone=""):
        if self.get_user_by_email(email):
            return None, "Email already registered."
        uid = str(uuid.uuid4())
        try:
            self.conn.execute(
                "INSERT INTO users(id,name,email,password,role,phone) VALUES(?,?,?,?,?,?)",
                (uid, name, email, _hash(password), role, phone)
            )
            self.conn.commit()
            return uid, None
        except sqlite3.IntegrityError as e:
            return None, str(e)

    def get_user_by_email(self, email):
        row = self.conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, uid):
        row = self.conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        return dict(row) if row else None

    def login(self, email, password):
        row = self.conn.execute(
            "SELECT * FROM users WHERE email=? AND password=? AND is_archived=0",
            (email, _hash(password))
        ).fetchone()
        return dict(row) if row else None

    def update_user(self, uid, name, phone):
        self.conn.execute("UPDATE users SET name=?, phone=? WHERE id=?", (name, phone, uid))
        self.conn.commit()

    def update_user_admin(self, uid, name, email, phone):
        """Admin/front-desk edit: also allows changing email, with a
        uniqueness check against every other account."""
        existing = self.conn.execute(
            "SELECT id FROM users WHERE email=? AND id!=?", (email, uid)
        ).fetchone()
        if existing:
            return False, "Another account already uses this email."
        self.conn.execute(
            "UPDATE users SET name=?, email=?, phone=? WHERE id=?",
            (name, email, phone, uid)
        )
        self.conn.commit()
        return True, None

    def get_all_users(self, role=None, include_archived=False):
        sql = "SELECT * FROM users WHERE 1=1"
        params = []
        if role:
            sql += " AND role=?"
            params.append(role)
        if not include_archived:
            sql += " AND is_archived=0"
        sql += " ORDER BY created_at DESC"
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def archive_user(self, uid):
        self.conn.execute("UPDATE users SET is_archived=1 WHERE id=?", (uid,))
        self.conn.commit()

    def unarchive_user(self, uid):
        self.conn.execute("UPDATE users SET is_archived=0 WHERE id=?", (uid,))
        self.conn.commit()

    # ════════════════════════════════════════════════
    # THERAPIST OPERATIONS
    # ════════════════════════════════════════════════
    def create_therapist_profile(self, user_id, **kwargs):
        tid = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO therapists(id,user_id,title,specialities,location,languages,
                price,free_available,online,in_person,rating,review_count,insurance,about,experience,education)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, user_id,
             kwargs.get("title",""),
             kwargs.get("specialities",""),
             kwargs.get("location",""),
             kwargs.get("languages","English"),
             kwargs.get("price", 0),
             kwargs.get("free_available", 0),
             kwargs.get("online", 1),
             kwargs.get("in_person", 1),
             kwargs.get("rating", 0.0),
             kwargs.get("review_count", 0),
             kwargs.get("insurance",""),
             kwargs.get("about",""),
             kwargs.get("experience",""),
             kwargs.get("education",""))
        )
        self.conn.commit()
        return tid

    def get_therapist_by_user(self, user_id):
        row = self.conn.execute(
            "SELECT t.*, u.name, u.email, u.phone FROM therapists t JOIN users u ON u.id=t.user_id WHERE t.user_id=?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_therapist_by_id(self, tid):
        row = self.conn.execute(
            "SELECT t.*, u.name, u.email, u.phone FROM therapists t JOIN users u ON u.id=t.user_id WHERE t.id=?",
            (tid,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_therapists(self, include_archived=False):
        sql = "SELECT t.*, u.name, u.email, u.is_archived FROM therapists t JOIN users u ON u.id=t.user_id"
        if not include_archived:
            sql += " WHERE u.is_archived=0"
        rows = self.conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def count_appointments_for_therapist(self, tid):
        row = self.conn.execute(
            "SELECT COUNT(*) as c FROM appointments WHERE therapist_id=?", (tid,)
        ).fetchone()
        return row["c"] if row else 0

    def delete_therapist(self, tid):
        """Hard-deletes a therapist account (user row, therapist profile,
        and their availability). Refuses if the therapist has any
        appointment history — archive instead in that case, so client
        booking history and payment records stay intact."""
        if self.count_appointments_for_therapist(tid) > 0:
            return False, "This therapist has appointment history and can't be deleted. Archive them instead."
        row = self.conn.execute("SELECT user_id FROM therapists WHERE id=?", (tid,)).fetchone()
        if not row:
            return False, "Therapist not found."
        user_id = row["user_id"]
        self.conn.execute("DELETE FROM availability WHERE therapist_id=?", (tid,))
        self.conn.execute("DELETE FROM waitlist WHERE therapist_id=?", (tid,))
        self.conn.execute("DELETE FROM therapists WHERE id=?", (tid,))
        if user_id:
            self.conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        self.conn.commit()
        return True, None

    def update_therapist(self, tid, **kwargs):
        fields = ["title","specialities","location","languages","price",
                  "free_available","online","in_person","insurance","about","experience","education"]
        sets   = ", ".join(f"{f}=?" for f in fields if f in kwargs)
        vals   = [kwargs[f] for f in fields if f in kwargs] + [tid]
        if sets:
            self.conn.execute(f"UPDATE therapists SET {sets} WHERE id=?", vals)
            self.conn.commit()

    def search_therapists(self, query="", speciality="", max_price=0,
                          online_only=False, free_only=False,
                          language="", insurance=""):
        sql = """SELECT t.*, u.name, u.email
                 FROM therapists t JOIN users u ON u.id=t.user_id
                 WHERE u.is_archived=0"""
        params = []
        if query:
            sql += " AND (u.name LIKE ? OR t.specialities LIKE ? OR t.location LIKE ? OR t.title LIKE ?)"
            q = f"%{query}%"
            params += [q, q, q, q]
        if speciality:
            sql += " AND t.specialities LIKE ?"
            params.append(f"%{speciality}%")
        if max_price > 0:
            sql += " AND t.price <= ?"
            params.append(max_price)
        if online_only:
            sql += " AND t.online=1"
        if free_only:
            sql += " AND t.free_available=1"
        if language:
            sql += " AND t.languages LIKE ?"
            params.append(f"%{language}%")
        if insurance:
            sql += " AND t.insurance LIKE ?"
            params.append(f"%{insurance}%")
        sql += " ORDER BY t.rating DESC"
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ════════════════════════════════════════════════
    # AVAILABILITY
    # ════════════════════════════════════════════════
    def set_availability(self, therapist_id, day, slots: list):
        self.conn.execute(
            "DELETE FROM availability WHERE therapist_id=? AND day_of_week=?",
            (therapist_id, day)
        )
        for slot in slots:
            self.conn.execute(
                "INSERT INTO availability(id,therapist_id,day_of_week,time_slot) VALUES(?,?,?,?)",
                (str(uuid.uuid4()), therapist_id, day, slot)
            )
        self.conn.commit()

    def get_availability(self, therapist_id):
        rows = self.conn.execute(
            "SELECT day_of_week, time_slot FROM availability WHERE therapist_id=? ORDER BY day_of_week, time_slot",
            (therapist_id,)
        ).fetchall()
        avail = {}
        for r in rows:
            avail.setdefault(r["day_of_week"], []).append(r["time_slot"])
        return avail

    def is_slot_booked(self, therapist_id, date_, time_):
        row = self.conn.execute(
            "SELECT 1 FROM appointments WHERE therapist_id=? AND date=? AND time=? AND status NOT IN ('cancelled')",
            (therapist_id, date_, time_)
        ).fetchone()
        return row is not None

    # ════════════════════════════════════════════════
    # APPOINTMENTS
    # ════════════════════════════════════════════════
    def create_appointment(self, client_id, therapist_id, date_, time_, type_, notes="", amount=0):
        if self.is_slot_booked(therapist_id, date_, time_):
            return None, "This slot has just been booked. Please choose another."
        aid = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO appointments(id,client_id,therapist_id,date,time,type,notes,amount) VALUES(?,?,?,?,?,?,?,?)",
            (aid, client_id, therapist_id, date_, time_, type_, notes, amount)
        )
        self.conn.commit()
        self._schedule_reminders(aid, date_, time_)
        return aid, None

    def _schedule_reminders(self, appointment_id, date_, time_):
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(f"{date_} {time_}", "%Y-%m-%d %H:%M")
            for delta, rtype in [(timedelta(hours=24), "email"), (timedelta(hours=1), "sms")]:
                remind_at = (dt - delta).strftime("%Y-%m-%d %H:%M")
                self.conn.execute(
                    "INSERT INTO reminders(id,appointment_id,remind_at,type) VALUES(?,?,?,?)",
                    (str(uuid.uuid4()), appointment_id, remind_at, rtype)
                )
            self.conn.commit()
        except Exception:
            pass

    def get_appointments_for_client(self, client_id):
        rows = self.conn.execute("""
            SELECT a.*, t.title as therapist_title, u.name as therapist_name,
                   t.id as therapist_id
            FROM appointments a
            JOIN therapists t ON t.id = a.therapist_id
            JOIN users u ON u.id = t.user_id
            WHERE a.client_id=?
            ORDER BY a.date DESC, a.time DESC""", (client_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_appointments_for_therapist(self, therapist_id):
        rows = self.conn.execute("""
            SELECT a.*, u.name as client_name, u.email as client_email, u.phone as client_phone
            FROM appointments a
            JOIN users u ON u.id = a.client_id
            WHERE a.therapist_id=?
            ORDER BY a.date ASC, a.time ASC""", (therapist_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_all_appointments(self):
        rows = self.conn.execute("""
            SELECT a.*, cu.name as client_name, tu.name as therapist_name
            FROM appointments a
            JOIN users cu ON cu.id=a.client_id
            JOIN therapists t ON t.id=a.therapist_id
            JOIN users tu ON tu.id=t.user_id
            ORDER BY a.date DESC, a.time DESC""").fetchall()
        return [dict(r) for r in rows]

    def update_appointment_status(self, aid, status):
        self.conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, aid))
        self.conn.commit()
        if status == "cancelled":
            return self._notify_waitlist_for_appointment(aid)
        return None

    def reschedule_appointment(self, aid, new_date, new_time):
        """Moves an existing upcoming appointment to a new date/time with
        the same therapist. Refuses if the appointment has already
        started/passed, or if the new slot is already taken. Re-schedules
        fresh 24h/1h reminders for the new time."""
        from datetime import datetime
        apt = self.conn.execute("SELECT * FROM appointments WHERE id=?", (aid,)).fetchone()
        if not apt:
            return False, "Appointment not found."
        apt = dict(apt)
        if apt["status"] not in ("confirmed", "pending"):
            return False, "Only upcoming appointments can be rescheduled."
        try:
            current_dt = datetime.strptime(f"{apt['date']} {apt['time']}", "%Y-%m-%d %H:%M")
            if current_dt <= datetime.now():
                return False, "This session has already started and can no longer be rescheduled."
        except ValueError:
            pass
        if new_date == apt["date"] and new_time == apt["time"]:
            return False, "Please choose a different date or time."
        if self.is_slot_booked(apt["therapist_id"], new_date, new_time):
            return False, "That slot is no longer available. Please choose another."

        self.conn.execute(
            "UPDATE appointments SET date=?, time=? WHERE id=?",
            (new_date, new_time, aid)
        )
        # drop any not-yet-sent reminders for the old time and schedule fresh ones
        self.conn.execute(
            "DELETE FROM reminders WHERE appointment_id=? AND sent=0", (aid,)
        )
        self.conn.commit()
        self._schedule_reminders(aid, new_date, new_time)
        return True, None

    def _notify_waitlist_for_appointment(self, appointment_id):
        """Marks the longest-waiting client as notified and returns their
        (client_id, client_name, client_email, therapist_name) info so the
        caller can send a notification email — or None if nobody's waiting."""
        row = self.conn.execute("SELECT therapist_id FROM appointments WHERE id=?", (appointment_id,)).fetchone()
        if not row: return None
        tid = row["therapist_id"]
        waiter = self.conn.execute(
            "SELECT * FROM waitlist WHERE therapist_id=? AND notified=0 ORDER BY added_at ASC LIMIT 1", (tid,)
        ).fetchone()
        if not waiter:
            return None
        self.conn.execute("UPDATE waitlist SET notified=1 WHERE id=?", (waiter["id"],))
        self.conn.commit()

        client = self.get_user_by_id(waiter["client_id"])
        therapist = self.get_therapist_by_id(tid)
        if not client or not therapist:
            return None
        return {
            "client_id":      client["id"],
            "client_name":    client["name"],
            "client_email":   client["email"],
            "therapist_name": therapist["name"],
        }

    # ════════════════════════════════════════════════
    # PAYMENTS
    # ════════════════════════════════════════════════
    def create_payment(self, appointment_id, client_id, therapist_id, amount,
                        method, status="completed", transaction_ref="",
                        insurance_provider=""):
        pid = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO payments(id,appointment_id,client_id,therapist_id,amount,
                method,status,transaction_ref,insurance_provider)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (pid, appointment_id, client_id, therapist_id, amount,
             method, status, transaction_ref, insurance_provider))
        self.conn.commit()
        return pid

    def get_payment_for_appointment(self, appointment_id):
        row = self.conn.execute(
            "SELECT * FROM payments WHERE appointment_id=? ORDER BY paid_at DESC LIMIT 1",
            (appointment_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_payments_for_client(self, client_id):
        rows = self.conn.execute("""
            SELECT p.*, u.name as therapist_name, a.date as appt_date, a.time as appt_time
            FROM payments p
            JOIN therapists t ON t.id = p.therapist_id
            JOIN users u ON u.id = t.user_id
            JOIN appointments a ON a.id = p.appointment_id
            WHERE p.client_id=?
            ORDER BY p.paid_at DESC""", (client_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_payments_for_therapist(self, therapist_id):
        rows = self.conn.execute("""
            SELECT p.*, u.name as client_name, a.date as appt_date, a.time as appt_time
            FROM payments p
            JOIN users u ON u.id = p.client_id
            JOIN appointments a ON a.id = p.appointment_id
            WHERE p.therapist_id=?
            ORDER BY p.paid_at DESC""", (therapist_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_all_payments(self):
        rows = self.conn.execute("""
            SELECT p.*, cu.name as client_name, tu.name as therapist_name,
                   a.date as appt_date, a.time as appt_time
            FROM payments p
            JOIN users cu ON cu.id = p.client_id
            JOIN therapists t ON t.id = p.therapist_id
            JOIN users tu ON tu.id = t.user_id
            JOIN appointments a ON a.id = p.appointment_id
            ORDER BY p.paid_at DESC""").fetchall()
        return [dict(r) for r in rows]

    def update_payment_status(self, pid, status):
        self.conn.execute("UPDATE payments SET status=? WHERE id=?", (status, pid))
        self.conn.commit()

    def get_revenue_by_month(self, therapist_id=None):
        """Returns list of (month_label, total) for completed payments, optionally scoped to one therapist."""
        sql = """SELECT substr(paid_at,1,7) as ym, SUM(amount) as total
                  FROM payments WHERE status='completed'"""
        params = []
        if therapist_id:
            sql += " AND therapist_id=?"
            params.append(therapist_id)
        sql += " GROUP BY ym ORDER BY ym"
        rows = self.conn.execute(sql, params).fetchall()
        return [(r["ym"], r["total"]) for r in rows]

    # ════════════════════════════════════════════════
    # EMAIL OUTBOX  (services/email_service.py does the actual sending;
    # this layer only persists the record of what was queued/sent)
    # ════════════════════════════════════════════════
    def queue_email(self, to_email, subject, body, related_appointment=None):
        eid = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO email_outbox(id,to_email,subject,body,related_appointment,status)
            VALUES(?,?,?,?,?,'pending')""",
            (eid, to_email, subject, body, related_appointment))
        self.conn.commit()
        return eid

    def mark_email_status(self, eid, status):
        from datetime import datetime
        self.conn.execute(
            "UPDATE email_outbox SET status=?, sent_at=? WHERE id=?",
            (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), eid)
        )
        self.conn.commit()

    def get_email_outbox(self, limit=200):
        rows = self.conn.execute(
            "SELECT * FROM email_outbox ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_due_reminders(self):
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = self.conn.execute("""
            SELECT r.*, a.client_id, a.therapist_id, a.date as appt_date,
                   a.time as appt_time, a.status as appt_status,
                   cu.name as client_name, cu.email as client_email,
                   tu.name as therapist_name
            FROM reminders r
            JOIN appointments a ON a.id = r.appointment_id
            JOIN users cu ON cu.id = a.client_id
            JOIN therapists t ON t.id = a.therapist_id
            JOIN users tu ON tu.id = t.user_id
            WHERE r.sent=0 AND r.remind_at<=? AND a.status IN ('confirmed','pending')
        """, (now,)).fetchall()
        return [dict(r) for r in rows]

    def mark_reminder_sent(self, reminder_id):
        self.conn.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
        self.conn.commit()

    # ════════════════════════════════════════════════
    # MESSAGES
    # ════════════════════════════════════════════════
    def send_message(self, sender_id, receiver_id, body):
        mid = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO messages(id,sender_id,receiver_id,body) VALUES(?,?,?,?)",
            (mid, sender_id, receiver_id, body)
        )
        self.conn.commit()
        return mid

    def get_conversation(self, user_a, user_b):
        rows = self.conn.execute("""
            SELECT m.*, u.name as sender_name
            FROM messages m JOIN users u ON u.id=m.sender_id
            WHERE (m.sender_id=? AND m.receiver_id=?)
               OR (m.sender_id=? AND m.receiver_id=?)
            ORDER BY m.sent_at ASC""", (user_a, user_b, user_b, user_a)).fetchall()
        return [dict(r) for r in rows]

    def get_conversations_for_user(self, user_id):
        """Return list of unique people the user has messaged with."""
        rows = self.conn.execute("""
            SELECT DISTINCT
                CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END AS other_id
            FROM messages
            WHERE sender_id=? OR receiver_id=?""", (user_id, user_id, user_id)).fetchall()
        result = []
        for r in rows:
            u = self.get_user_by_id(r["other_id"])
            if u: result.append(u)
        return result

    def mark_messages_read(self, sender_id, receiver_id):
        self.conn.execute(
            "UPDATE messages SET is_read=1 WHERE sender_id=? AND receiver_id=?",
            (sender_id, receiver_id)
        )
        self.conn.commit()

    def unread_count(self, user_id):
        row = self.conn.execute(
            "SELECT COUNT(*) as c FROM messages WHERE receiver_id=? AND is_read=0", (user_id,)
        ).fetchone()
        return row["c"] if row else 0

    # ════════════════════════════════════════════════
    # WAITLIST
    # ════════════════════════════════════════════════
    def add_to_waitlist(self, client_id, therapist_id):
        exists = self.conn.execute(
            "SELECT 1 FROM waitlist WHERE client_id=? AND therapist_id=?", (client_id, therapist_id)
        ).fetchone()
        if exists: return False, "Already on waitlist."
        self.conn.execute(
            "INSERT INTO waitlist(id,client_id,therapist_id) VALUES(?,?,?)",
            (str(uuid.uuid4()), client_id, therapist_id)
        )
        self.conn.commit()
        return True, None

    def get_waitlist_for_client(self, client_id):
        rows = self.conn.execute("""
            SELECT w.*, u.name as therapist_name, t.id as therapist_id
            FROM waitlist w
            JOIN therapists t ON t.id=w.therapist_id
            JOIN users u ON u.id=t.user_id
            WHERE w.client_id=? ORDER BY w.added_at ASC""", (client_id,)).fetchall()
        return [dict(r) for r in rows]

    def remove_from_waitlist(self, wid):
        self.conn.execute("DELETE FROM waitlist WHERE id=?", (wid,))
        self.conn.commit()

    # ════════════════════════════════════════════════
    # ADMIN / STATS
    # ════════════════════════════════════════════════
    def get_stats(self):
        def count(sql, *p): return self.conn.execute(sql,p).fetchone()[0]
        return {
            "total_users":        count("SELECT COUNT(*) FROM users"),
            "total_clients":      count("SELECT COUNT(*) FROM users WHERE role='client'"),
            "total_therapists":   count("SELECT COUNT(*) FROM users WHERE role='therapist'"),
            "total_appointments": count("SELECT COUNT(*) FROM appointments"),
            "confirmed":          count("SELECT COUNT(*) FROM appointments WHERE status='confirmed'"),
            "completed":          count("SELECT COUNT(*) FROM appointments WHERE status='completed'"),
            "cancelled":          count("SELECT COUNT(*) FROM appointments WHERE status='cancelled'"),
            "waitlist_entries":   count("SELECT COUNT(*) FROM waitlist"),
            "total_revenue":      self.conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM appointments WHERE status='completed'"
            ).fetchone()[0],
        }

    def delete_user(self, uid):
        self.conn.execute("DELETE FROM users WHERE id=?", (uid,))
        self.conn.commit()
