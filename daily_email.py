import schedule
import time
import logging
import os
import json
import urllib.request
from datetime import datetime

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "SG.CsnmLvATRHKWlC7qD4BA1w.GqNskQwNrzoAxtEOc20RMvWwE02u1zMiJXjdgt-BlM")
SENDER_EMAIL = os.environ.get("GMAIL_SENDER", "martin.dailerian@gmail.com")
SEND_TIME = "16:00"

RECIPIENTS = [
    "andredailerian37@gmail.com",
    "andredailerian@chatham-nj.org",
    "monika.a.grabania@gmail.com",
    "Monika.Grabania@vitaminshoppe.com",
    "martin.dailerian@jpmchase.com",
    "arinadailerian@chatham-nj.org",
]

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)

ANDRE_GRADES = [
    {"subject": "Honors English 10",       "teacher": "Agelis, Nicholas",  "mp1": 75.0,  "current": 83.3,  "letter": "B"},
    {"subject": "US History 2A",           "teacher": "Nagy, Brian",       "mp1": 81.8,  "current": 69.3,  "letter": "D"},
    {"subject": "Spanish 3",               "teacher": "Fix, Marlin",       "mp1": 83.4,  "current": 90.6,  "letter": "A"},
    {"subject": "Chemistry A (lab)",       "teacher": "Naumova, Yelena",   "mp1": 78.6,  "current": 82.1,  "letter": "B"},
    {"subject": "Algebra 2A",              "teacher": "Cordano, Dagmar",   "mp1": 72.5,  "current": 77.6,  "letter": "C"},
    {"subject": "Experiencing Fine Art",   "teacher": "Hull, Candace",     "mp1": None,  "current": 94.7,  "letter": "A"},
    {"subject": "Health / PE / Driver Ed", "teacher": "Picariello, Evan",  "mp1": 98.0,  "current": 100.0, "letter": "A"},
]

ARINA_GRADES = [
    {"subject": "Band 7",                     "teacher": "Spriggs, Christie", "mp_prev": 97.0, "current": 95.9, "letter": "A"},
    {"subject": "Dream Room Design Lab",      "teacher": "Hitchings, James",  "mp_prev": None, "current": 96.9, "letter": "A"},
    {"subject": "English 7 Honors",           "teacher": "Iannuzzi, George",  "mp_prev": 79.9, "current": 81.4, "letter": "B"},
    {"subject": "Health 7",                   "teacher": "Nydegger, Kelly",   "mp_prev": None, "current": 92.5, "letter": "A"},
    {"subject": "Mathematics Honors 7",       "teacher": "Novick, Amanda",    "mp_prev": 89.5, "current": 80.0, "letter": "B"},
    {"subject": "Physical Education 7",       "teacher": "Murphy, Liam",      "mp_prev": 100,  "current": 100,  "letter": "A"},
    {"subject": "Science 7",                  "teacher": "LoPorto, Lauren",   "mp_prev": 91.5, "current": 85.8, "letter": "B"},
    {"subject": "World Cultures & Geography", "teacher": "Becker, Carly",     "mp_prev": 94.0, "current": 93.8, "letter": "A"},
    {"subject": "French 7",                   "teacher": "Engell, Tine",      "mp_prev": 92.4, "current": 90.7, "letter": "A"},
]

ANDRE_ASSIGNMENTS = {
    "overdue": [{"title": "Voice From My Lai", "subject": "US History 2A", "due": "Feb 12"}],
    "upcoming": [
        {"title": "HWK: unit packet pages 3,6-7", "subject": "Chemistry A", "due": "Mon 3/16"},
        {"title": "Test CH 5 Part 2",              "subject": "Algebra 2A",  "due": "Mon 3/16"},
        {"title": "HWK: Finish lab analysis",      "subject": "Chemistry A", "due": "Tue 3/17"},
        {"title": "Read chapter 12",               "subject": "English 10",  "due": "Tue 3/17"},
        {"title": "HWK: unit packet pages 8-9",    "subject": "Chemistry A", "due": "Wed 3/18"},
        {"title": "LAB QUIZ: Ionic compounds",      "subject": "Chemistry A", "due": "Mon 3/23"},
    ],
}

GRADE_COLORS = {
    "A": ("#EAF3DE", "#27500A"), "B": ("#E6F1FB", "#0C447C"),
    "C": ("#FAEEDA", "#633806"), "D": ("#FCEBEB", "#791F1F"),
}

def detect_alerts():
    alerts = []
    for c in ANDRE_GRADES:
        if c["current"] < 75:
            alerts.append(f"Andre - {c['subject']} is at {c['current']:.1f} (below 75)")
        if c["mp1"] and (c["current"] - c["mp1"]) <= -5:
            alerts.append(f"Andre - {c['subject']} dropped {abs(c['current']-c['mp1']):.1f} pts")
    for c in ARINA_GRADES:
        if c["mp_prev"] and (c["current"] - c["mp_prev"]) <= -5:
            alerts.append(f"Arina - {c['subject']} dropped {abs(c['current']-c['mp_prev']):.1f} pts")
    for a in ANDRE_ASSIGNMENTS.get("overdue", []):
        alerts.append(f"OVERDUE: Andre - {a['title']} ({a['subject']}, due {a['due']})")
    return alerts

def grade_badge(letter, score):
    bg, fg = GRADE_COLORS.get(letter[0], ("#eee", "#333"))
    s = f"{score:.1f}" if score else "-"
    return (f'<span style="background:{bg};color:{fg};padding:3px 10px;'
            f'border-radius:99px;font-family:monospace;font-size:13px;'
            f'font-weight:600;">{letter} {s}</span>')

def assign_cell(subject, assignments):
    items = []
    for a in assignments.get("overdue", []):
        if any(w in a["subject"].lower() for w in subject.lower().split()):
            items.append(f'<span style="color:#791F1F;font-size:12px;">OVERDUE: {a["title"]} (due {a["due"]})</span>')
    for a in assignments.get("upcoming", []):
        if any(w in a["subject"].lower() for w in subject.lower().split()):
            items.append(f'<span style="color:#0C447C;font-size:12px;">Due {a["due"]}: {a["title"]}</span>')
    return "<br>".join(items) if items else '<span style="color:#aaa;font-size:12px;">Nothing due</span>'

def build_rows(grades, assignments=None):
    rows = ""
    for i, c in enumerate(grades):
        bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        badge = grade_badge(c["letter"], c["current"])
        assign = assign_cell(c["subject"], assignments) if assignments else '<span style="color:#aaa;font-size:12px;">-</span>'
        rows += (f"<tr style='background:{bg};'>"
                 f"<td style='padding:10px 14px;border-bottom:1px solid #eee;font-size:13px;'>"
                 f"<strong>{c['subject']}</strong><br>"
                 f"<span style='color:#888;font-size:11px;'>{c['teacher']}</span></td>"
                 f"<td style='padding:10px 14px;border-bottom:1px solid #eee;text-align:center;'>{badge}</td>"
                 f"<td style='padding:10px 14px;border-bottom:1px solid #eee;font-size:12px;line-height:1.6;'>{assign}</td></tr>")
    return rows

def build_email():
    today = datetime.now().strftime("%A, %B %-d, %Y")
    alerts = detect_alerts()
    alert_html = ""
    if alerts:
        items = "".join(f"<li style='margin-bottom:6px;'>{a}</li>" for a in alerts)
        alert_html = (f'<div style="background:#fff3cd;border-left:4px solid #ffc107;'
                       f'padding:14px 18px;margin-bottom:24px;border-radius:6px;">'
                       f'<strong style="color:#856404;">Alerts requiring attention</strong>'
                       f'<ul style="margin:8px 0 0;padding-left:18px;color:#856404;font-size:13px;">{items}</ul></div>')
    th = ('style="padding:9px 14px;font-size:11px;color:#555;text-align:left;'
          'text-transform:uppercase;border-bottom:1px solid #e8e8e8;background:#f0f4fa;"')
    ts = ('width="100%" cellpadding="0" cellspacing="0" '
          'style="border:1px solid #e8e8e8;border-radius:8px;overflow:hidden;border-collapse:collapse;"')
    a_rows  = build_rows(ANDRE_GRADES, ANDRE_ASSIGNMENTS)
    ar_rows = build_rows(ARINA_GRADES, None)
    status  = "Action Required" if alerts else "All Good"
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<BODY style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:24px 0;">
<tr><td align="center"><table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;">
<tr><td style="background:#1a3a6b;border-radius:10px 10px 0 0;padding:24px 28px;">
<table width="100%"><tr>
<td><span style="color:#fff;font-size:20px;font-weight:600;">Dailerian <span style="color:#7eb8f7;">School</span> Tracker</span><br>
<span style="color:#a8c4e8;font-size:12px;">{today} - Daily Summary</span></td>
<td align="right"><span style="background:#2d5a9e;color:#a8c4e8;font-size:11px;padding:4px 10px;border-radius:4px;">{status}</span></td>
</tr></table></td></tr>
<tr><td style="background:#fff;padding:28px;border-radius:0 0 10px 10px;">{alert_html}
<table {ts}>
<tr><td colspan="3" style="padding:12px 14px;background:#f7f9fc;border-bottom:1px solid #e8e8e8;">
<strong style="font-size:15px;">AD - Andre Dailerian</strong>
<span style="color:#888;font-size:12px;margin-left:8px;">Grade 10 - Chatham HS - GPA 2.97</span></td></tr>
<tr><th {th} width="35%">Subject</th><th {th} width="15%" style="text-align:center;">Grade</th><th {th}>Due This Week</th></tr>
{a_rows}</table><br>
<table {ts}>
<tr><td colspan="3" style="padding:12px 14px;background:#f7f9fc;border-bottom:1px solid #e8e8e8;">
<strong style="font-size:15px;">AR - Arina Dailerian</strong>
<span style="color:#888;font-size:12px;margin-left:8px;">Grade 7 - Chatham MS - GPA 3.79</span></td></tr>
<tr><th {th} width="35%">Subject</th><th {th} width="15%" style="text-align:center;">Grade</th><th {th}>Due This Week</th></tr>
{ar_rows}</table>
</td></tr>
<tr><td style="padding:16px 0;text-align:center;">
<span style="font-size:11px;color:#aaa;">Dailerian School Tracker - Sent daily at 4:00 PM</span>
</td></tr></table></td></tr></table></BODY></html>"""

def send_email():
    alerts  = detect_alerts()
    html    = build_email()
    today   = datetime.now().strftime("%A %b %-d")
    flag    = "Action Required" if alerts else "All Good"
    subject = f"Dailerian School Tracker - {today} - {flag}"
    payload = json.dumps({
        "personalizations": [{"to": [{"email": r} for r in RECIPIENTS]}],
        "from": {"email": SENDER_EMAIL, "name": "Dailerian School Tracker"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        log.info(f"Email sent! SendGrid status: {resp.status} to {len(RECIPIENTS)} recipients.")

def run_daily_job():
    log.info("=" * 50)
    log.info("Running Dailerian School Tracker daily job...")
    try:
        send_email()
        log.info("Daily job complete.")
    except Exception as e:
        log.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    log.info(f"Started. Scheduled daily at {SEND_TIME}.")
    run_daily_job()
    schedule.every().day.at(SEND_TIME).do(run_daily_job)
    while True:
        schedule.run_pending()
        time.sleep(30)
