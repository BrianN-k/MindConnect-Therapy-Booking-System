"""Seed the database with demo data (runs once — skipped if data already exists)."""


def seed_database(db):
    if db.get_user_by_email("amina@example.com"):
        return   # already seeded

    # ── users ────────────────────────────────────────
    c1, _ = db.create_user("Amina Odhiambo",  "amina@example.com",  "pass123", "client",    "+254712345678")
    c2, _ = db.create_user("James Mutua",     "james@example.com",  "pass123", "client",    "+254722345678")
    c3, _ = db.create_user("Grace Wanjiku",   "grace@example.com",  "pass123", "client",    "+254733901234")
    t1u, _ = db.create_user("Dr. Sarah Kamau", "sarah@example.com",  "pass123", "therapist", "+254733345678")
    t2u, _ = db.create_user("Dr. Kevin Otieno","kevin@example.com",  "pass123", "therapist", "+254744345678")
    t3u, _ = db.create_user("Dr. Fatuma Hassan","fatuma@example.com","pass123", "therapist", "+254755345678")
    t4u, _ = db.create_user("Mr. Brian Wachira","brian@example.com", "pass123", "therapist", "+254766345678")
    db.create_user("Admin",               "admin@mindconnect.ke","admin123","admin",    "+254700000000")

    # ── therapist profiles ───────────────────────────
    t1 = db.create_therapist_profile(t1u,
        title="Clinical Psychologist",
        specialities="Anxiety,Depression,CBT,Trauma",
        location="Westlands, Nairobi",
        languages="English,Swahili",
        price=2500, free_available=0, online=1, in_person=1,
        rating=4.9, review_count=47,
        insurance="NHIF,AAR,Jubilee",
        about="Licensed clinical psychologist with 8+ years of experience helping individuals manage anxiety, depression, and trauma using evidence-based CBT. I believe in a safe, non-judgmental space where healing can happen at your own pace.",
        experience="8 years",
        education="PhD Clinical Psychology, University of Nairobi")

    t2 = db.create_therapist_profile(t2u,
        title="Counselling Psychologist",
        specialities="Stress,Relationships,Grief,Addiction",
        location="Karen, Nairobi",
        languages="English,Swahili,Luo",
        price=2000, free_available=1, online=1, in_person=1,
        rating=4.7, review_count=32,
        insurance="NHIF,Britam",
        about="I specialise in helping people navigate life's most challenging transitions — grief, relationship difficulties, stress, and addiction recovery. My approach is person-centred and culturally sensitive.",
        experience="6 years",
        education="MSc Counselling Psychology, Kenyatta University")

    t3 = db.create_therapist_profile(t3u,
        title="Family & Couples Therapist",
        specialities="Family Therapy,Couples,Parenting,PTSD",
        location="Kilimani, Nairobi",
        languages="English,Swahili,Arabic",
        price=3000, free_available=0, online=0, in_person=1,
        rating=4.8, review_count=61,
        insurance="AAR,Jubilee,Madison",
        about="Specialising in family systems therapy and couples counselling, I help families and partnerships rebuild communication, trust, and connection with trauma-informed care.",
        experience="11 years",
        education="PhD Family Therapy, Aga Khan University")

    t4 = db.create_therapist_profile(t4u,
        title="Psychotherapist",
        specialities="Youth,School Issues,ADHD,Self-esteem",
        location="Thika Road, Nairobi",
        languages="English,Swahili,Kikuyu",
        price=1500, free_available=1, online=1, in_person=1,
        rating=4.6, review_count=28,
        insurance="NHIF",
        about="Working primarily with adolescents and young adults, I help build emotional resilience, manage school pressures, ADHD, and self-esteem challenges.",
        experience="5 years",
        education="MSc Psychotherapy, Daystar University")

    # ── availability ─────────────────────────────────
    slots_am  = ["09:00","10:00","11:00"]
    slots_pm  = ["14:00","15:00","16:00"]
    slots_all = slots_am + slots_pm

    for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]:
        db.set_availability(t1, day, slots_all if day != "Friday" else slots_am)

    for day, slots in [("Monday", slots_am), ("Wednesday", slots_all), ("Friday", slots_all), ("Saturday", slots_am)]:
        db.set_availability(t2, day, slots)

    for day, slots in [("Tuesday", slots_pm), ("Thursday", slots_all), ("Saturday", slots_am)]:
        db.set_availability(t3, day, slots)

    for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]:
        db.set_availability(t4, day, ["15:00","16:00","17:00"])

    # ── appointments (spanning a few months so charts have data) ──
    a1, _ = db.create_appointment(c1, t1, "2026-07-28", "10:00", "online",     "First session", 2500)
    a2, _ = db.create_appointment(c1, t1, "2026-07-15", "11:00", "online",     "Follow-up",     2500)
    a3, _ = db.create_appointment(c2, t2, "2026-07-29", "14:00", "in-person",  "",              2000)
    a4, _ = db.create_appointment(c3, t3, "2026-07-30", "10:00", "in-person",  "Couples intake",3000)
    a5, _ = db.create_appointment(c2, t1, "2026-06-10", "09:00", "online",     "",              2500)
    a6, _ = db.create_appointment(c3, t4, "2026-06-18", "16:00", "online",     "",              1500)
    a7, _ = db.create_appointment(c1, t2, "2026-05-20", "10:00", "in-person",  "",              2000)
    a8, _ = db.create_appointment(c2, t3, "2026-05-05", "14:00", "in-person",  "",              3000)

    if a2: db.update_appointment_status(a2, "completed")
    if a3: db.update_appointment_status(a3, "pending")
    if a5: db.update_appointment_status(a5, "completed")
    if a6: db.update_appointment_status(a6, "completed")
    if a7: db.update_appointment_status(a7, "completed")
    if a8: db.update_appointment_status(a8, "completed")

    # ── payments ──────────────────────────────────────
    if a1: db.create_payment(a1, c1, t1, 2500, "mpesa",     "completed", "MC482913")
    if a2: db.create_payment(a2, c1, t1, 2500, "card",      "completed", "MC118820")
    if a3: db.create_payment(a3, c2, t2, 2000, "insurance", "pending",   "MC334410", insurance_provider="NHIF")
    if a4: db.create_payment(a4, c3, t3, 3000, "cash",      "pending",   "MC559021")
    if a5: db.create_payment(a5, c2, t1, 2500, "mpesa",     "completed", "MC671288")
    if a6: db.create_payment(a6, c3, t4, 1500, "mpesa",     "completed", "MC790112")
    if a7: db.create_payment(a7, c1, t2, 2000, "card",      "completed", "MC802234")
    if a8: db.create_payment(a8, c2, t3, 3000, "insurance", "completed", "MC901345", insurance_provider="AAR")

    # ── messages ─────────────────────────────────────
    db.send_message(c1, t1u, "Hello Dr. Kamau, I just booked my first session. What should I prepare?")
    db.send_message(t1u, c1, "Welcome Amina! No special preparation needed. Just come with an open mind.")
    db.send_message(c1, t1u, "Thank you, that's reassuring. See you Monday!")
    db.send_message(c2, t2u, "Dr. Otieno, is the Tuesday slot still available?")
    db.send_message(t2u, c2, "Hi James, yes it is! I've reserved it for you.")

    # ── waitlist ─────────────────────────────────────
    db.add_to_waitlist(c1, t3)
    db.add_to_waitlist(c3, t2)

    # ── demo email outbox entries (so Admin > Email Notifications
    #    has something to show immediately, without waiting for the
    #    background scheduler or a real SMTP server) ─────────────
    demo_emails = [
        (db.get_user_by_id(c1)["email"], "Appointment confirmed with Dr. Sarah Kamau",
         "Hi Amina,\n\nYour appointment has been confirmed for 28 July at 10:00 AM.\n\n— MindConnect"),
        (db.get_user_by_id(c1)["email"], "Payment receipt — KSh 2,500",
         "Hi Amina,\n\nWe've received your M-Pesa payment of KSh 2,500.\nRef: MC482913\n\n— MindConnect"),
        (db.get_user_by_id(c2)["email"], "New booking from James Mutua",
         "Hi Dr. Otieno,\n\nYou have a new booking for 29 July at 2:00 PM.\n\n— MindConnect"),
        (db.get_user_by_id(c3)["email"], "Reminder: your session with Dr. Fatuma Hassan is coming up",
         "Hi Grace,\n\nThis is a reminder that your session is tomorrow at 10:00 AM.\n\n— MindConnect"),
    ]
    for to_email, subject, body in demo_emails:
        eid = db.queue_email(to_email, subject, body)
        db.mark_email_status(eid, "demo_logged")
