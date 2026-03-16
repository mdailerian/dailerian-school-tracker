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
    "martin@dailerian.com",
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
    {"subject": "Health 7",                    "teacher": "Nydegger, Kelly",   "mp_prev": None, "current": 92.5, "letter": "A"},
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
        {"title": "Test CH 58Pa$ Part 2",              "subject": "Algebra 2A",  "due": "Mon 3/16"},
        {"title": "HWK: Finish lab analysis",        "subject": "Chemistry A", "due": "Tue 3/17"},
        {"title": "Read chapter 12",                 "subject": "English 10",  "due": "Tue 3/17"},
        {"title": "HWK: unit packet pages 8-9",      "subject": "Chemistry A", "due": "Wed 3/18"},
        {"title": "LABQUNIZ: Ionic compounds",       "subject": "Chemistry A", "due": "Mon 3/23"},
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
    return (f'<span style="background:{bg};color:{fg};padding:2px 6px;'
            f'border-radius:3px;font-family:monospace;font-size:10px;font-weight:bold;">'
            f'{letter} {s}</span>')

def assign_cell(subject, assignments):
    items = []
    seen = set()
    sl = subject.lower()
    for a in assignments.get("overdue", []):
        al = a["subject"].lower()
        if al in sl or sl in al:
            if a["title"] not in seen:
                seen.add(a["title"])
                items.append(f'<span style="color:#791F1F;font-size:10px;">&#9888; {a["title"]} ({a["due"]})</span>')
    for a in assignments.get("upcoming", []):
        al = a["subject"].lower()
        if al in sl or sl in al:
            if a["title"] not in seen:
                seen.add(a["title"])
                items.append(f'<span style="color:#0C447C;font-size:10px;">{a["due"]}: {a["title"]}</span>')
    return "<br>".join(items) if items else '<span style="color:#aaa;font-size:10px;">Nothing due</span>'

def build_rows(grades, assignments=None):
    rows = ""
    for i, c in enumerate(grades):
        assign = assign_cell(c["subject"], assignments) if assignments else None
        if assignments and assign == '<span style="color:#aaa;font-size:10px;">Nothing due</span>':
            continue
        bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        badge = grade_badge(c["letter"], c["current"])
        assign_html = assign if assign else '<span style="color:#aaa;font-size:10px;">-</span>'
        rows += (f"<tr style='background:{bg};'>"
                 f"<td style='padding:3px 8px;border-bottom:1px solid #eee;font-size:10px;'>"
                 f"<strong style='color:#222;'>{c['subject']}</strong></td>"
                 f"<td style='padding:3px 8px;border-bottom:1px solid #eee;text-align:center;'>{badge}</td>"
                 f"<td style='padding:3px 8px;border-bottom:1px solid #eee;font-size:10px;line-height:1.4;'>{assign_html}</td></tr>")
    if not rows and assignments:
        rows = "<tr><td colspan='3' style='padding:6px 8px;text-align:center;color:#27500A;font-size:10px;'>&#10003; All clear!</td></tr>"
    return rows

def build_email():
    today = datetime.now().strftime("%a %b %-d, %Y")
    alerts = detect_alerts()
    alert_html = ""
    if alerts:
        items = "".join(
            f"<tr><td style='padding:2px 8px;font-size:10px;color:#856404;'>&#9888; {a}</td></tr>"
            for a in alerts)
        alert_html = (f'<table width="100%" cellpadding="0" cellspacing="0" '
                      f'style="background:#fff3cd;border:1px solid #ffc107;border-radius:3px;margin-bottom:6px;">'
                      f'<tr><td style="padding:3px 8px;font-size:10px;font-weight:bold;color:#856404;">ALERTS</td></tr>'
                      f'{items}</table>')

    th = ('style="padding:3px 8px;font-size:9px;color:#555;text-align:left;'
          'text-transform:uppercase;border-bottom:1px solid #ddd;background:#f0f4fa;letter-spacing:0.3px;"')
    ts = ('width="100%" cellpadding="0" cellspacing="0" '
          'style="border:1px solid #ddd;border-radius:3px;overflow:hidden;border-collapse:collapse;margin-bottom:6px;"')
    a_rows  = build_rows(ANDRE_GRADES, ANDRE_ASSIGNMENTS)
    ar_rows = build_rows(ARINA_GRADES, None)
    status  = "&#9888; Action Required" if alerts else "&#10003; All Good"

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  @media print {{
    body {{ margin:0; padding:4px; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    table {{ page-break-inside:avoid; }}
  }}
</style>
</head>
<body style="margin:0;padding:6px;background:#fff;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:0 auto;">

<tr><td style="background:#1a3a6b;border-radius:3px 3px 0 0;padding:6px 10px;">
<table width="100%"><tr>
<td><span style="color:#fff;font-size:13px;font-weight:bold;">Dailerian <span style="color:#7eb8f7;">School</span> Tracker</span>
<span style="color:#a8c4e8;font-size:10px;margin-left:8px;">{today}</span></td>
<td align="right"><span style="background:#2d5a9e;color:#a8c4e8;font-size:10px;padding:2px 6px;border-radius:2px;">{status}</span></td>
</tr></table>
</td></tr>

<tr><td style="background:#fff;padding:6px 4px 2px 4px;">
{alert_html}
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td width="50%" style="padding-right:3px;vertical-align:top;">
<table {ts}>
<tr><td colspan="3" style="padding:3px 8px;background:#e6f1fb;border-bottom:1px solid #ddd;">
<span style="font-size:11px;font-weight:bold;color:#0c447c;">Andre Dailerian</span>
<span style="color:#555;font-size:9px;margin-left:4px;">Gr.10 &bull; GPA 2.97</span>
</td></tr>
<tr><th {th} width="42%">Subject</th><th {th} width="18%" style="text-align:center;">Grade</th><th {th}>Due</th></tr>
{a_rows}
</table>
</td>
<td width="50%" style="padding-left:3px;vertical-align:top;">
<table {ts}>
<tr><td colspan="3" style="padding:3px 8px;background:#fbeaf0;border-bottom:1px solid #ddd;">
<span style="font-size:11px;font-weight:bold;color:#72243e;">Arina Dailerian</span>
<span style="color:#555;font-size:9px;margin-left:4px;">Gr.7 &bull; GPA 3.79</span>
</td></tr>
<tr><th {th} width="42%">Subject</th><th {th} width="18%" style="text-align:center;">Grade</th><th {th}>Due</th></tr>
{ar_rows}
</table>
</td>
</tr>
</table>
</td></tr>

<tr><td style="padding:3px;text-align:center;border-top:1px solid #eee;">
<span style="font-size:9px;color:#aaa;">Dailerian School Tracker &bull; Daily 4:00 PM &bull; Chatham School District</span>
</td></tr>
</table>
</body></html>"""

def send_email():
    alerts  = detect_alerts()
    html    = build_email()
    today   = datetime.now().strftime("%a %b %-d")
    flag    = "Action Required" if alerts else "All Good"
    subject = f"Dailerian School Tracker - {today} - {flag}"
    payload = json.dumps({
        "personalizations": [{"to": [{"email": r} for r in RECIPIENTS]}],
        "from": {"email": SENDER_EMAIL, "name": "Dailerian School Tracker"},
        "subject":subject,
        "content": [{"type": "text/html", "value": html}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        log.info(f"Email sent!!SendGrid status: {resp.status} to {len(RECIPIENTS)} recipients.")

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
