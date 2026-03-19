import schedule
import time
import logging
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

SENDGRID_API_KEY  = os.environ.get("SENDGRID_API_KEY", "")
SENDER_EMAIL      = os.environ.get("GMAIL_SENDER", "martin.dailerian@gmail.com")
TEXTBELT_KEY      = os.environ.get("TEXTBELT_KEY", "")
ANDRE_PHONE       = os.environ.get("ANDRE_PHONE", "+16462442292")
GENESIS_USER      = os.environ.get("GENESIS_USER", "martin@dailerian.com")
GENESIS_PASS      = os.environ.get("GENESIS_PASS", "")
ANDRE_ID          = "20286810"
ARINA_ID          = "20316811"
SEND_TIME         = "16:00"

# SMS_RECIPIENTS: comma-separated list in Railway env var
# e.g. "+16462442292,+19085147364,+16462442253"
_sms_env = os.environ.get("SMS_RECIPIENTS", "+16462442292,+19085147364,+16462442253")
ANDRE_PHONES = [p.strip() for p in _sms_env.split(",") if p.strip()]

# EMAIL_RECIPIENTS: comma-separated list in Railway env var
# e.g. "a@b.com,c@d.com"
_email_env = os.environ.get(
    "EMAIL_RECIPIENTS",
    "andredailerian37@gmail.com,andredailerian@chatham-nj.org,monika.a.grabania@gmail.com,Monika.Grabania@vitaminshoppe.com,martin.dailerian@jpmchase.com,arinadailerian@chatham-nj.org,martin@dailerian.com"
)
EMAIL_RECIPIENTS = [e.strip() for e in _email_env.split(",") if e.strip()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)

GRADE_COLORS = {
    "A": ("#EAF3DE", "#27500A"),
    "B": ("#E6F1FB", "#0C447C"),
    "C": ("#FAEEDA", "#633806"),
    "D": ("#FCEBEB", "#791F1F"),
}

SUBJECT_SHORT = {
    "honors english 10": "ENG",
    "us history 2 a": "HIST",
    "us history 2a": "HIST",
    "spanish 3": "SPA",
    "chemistry a (lab)": "CHEM",
    "chemistry a": "CHEM",
    "algebra 2 a": "ALG",
    "algebra 2a": "ALG",
    "experiencing fine art": "ART",
    "comprehensive health/phys ed/driver ed 10": "PE",
    "health / pe / driver ed": "PE",
    "english 10": "ENG",
}


def genesis_login():
    import http.cookiejar
    import ssl
    jar = http.cookiejar.CookieJar()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ctx),
    )
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Language", "en-US,en;q=0.5"),
        ("Connection", "keep-alive"),
    ]
    # Step 1: GET the login page to pick up any pre-login cookies
    opener.open("https://parents.chatham-nj.org/genesis/sis/view?gohome=true")
    # Step 2: POST credentials
    data = urllib.parse.urlencode({
        "j_username": GENESIS_USER,
        "j_password": GENESIS_PASS,
        "idTokenString": "",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://parents.chatham-nj.org/genesis/sis/j_security_check?parents=Y",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Referer": "https://parents.chatham-nj.org/genesis/sis/view?gohome=true"},
    )
    opener.open(req)
    log.info("Genesis login successful.")
    return opener


def parse_grades(html, student_name):
    """Parse grades from Genesis gradebook HTML using regex - handles any HTML structure."""
    import re
    grades = []
    # Strip all HTML tags to get plain text
    text = re.sub(r'<[^>]+>', ' ', html)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)

    # Find the notecard section - everything between student name and footer
    # Look for the block that contains marking period patterns like MP1, MP2 etc
    # Pattern: term | CourseName ... teacher ... MP1 date MP2 date grade grade
    # Extract all spans of text that look like: FY | CourseName or S2 | CourseName
    term_pat = re.compile(
        r'(FY|S1|S2|Q1|Q2|Q3|Q4)\s*\|\s*'  # term
        r'([A-Za-z][^\n]{3,60?})\n'           # course name (non-greedy)
    )
    # Simpler approach: find all grade values associated with MP periods
    # The page text looks like:
    # "Honors English 10 ... MP1 8/25 to 1/23 MP2 1/24 to 6/16 75.00 84.00"
    # Extract course blocks between "FY |" or "S2 |" markers
    blocks = re.split(r'(?:FY|S1|S2|Q1|Q2|Q3|Q4)\s*\|', text)
    if len(blocks) < 2:
        log.warning(f"Could not find term markers in HTML for {student_name}. len={len(text)}")
        return []

    for block in blocks[1:]:  # skip first (before any course)
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
        # First non-empty line is the course name
        course_name = lines[0].strip()
        if len(course_name) < 3 or len(course_name) > 80:
            continue
        # Find all grade values (numbers like 75.00, 84.00) in the block
        grade_vals = re.findall(r'\b(\d{2,3}\.\d{2})\b', block)
        grade_floats = []
        for g in grade_vals:
            try:
                v = float(g)
                if 0 <= v <= 100:
                    grade_floats.append(v)
            except ValueError:
                pass
        if not grade_floats:
            continue
        current = grade_floats[-1]
        prev = grade_floats[-2] if len(grade_floats) >= 2 else None
        grades.append({
            "subject": course_name,
            "current": current,
            "prev": prev,
            "letter": score_to_letter(current),
        })

    log.info(f"Parsed {len(grades)} courses for {student_name}.")
    return grades

def score_to_letter(score):
    if score is None: return "N/A"
    if score >= 89.5: return "A"
    if score >= 79.5: return "B"
    if score >= 69.5: return "C"
    if score >= 59.5: return "D"
    return "F"


def calc_gpa(grades):
    gpa_map = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
    vals = [gpa_map[g["letter"]] for g in grades if g["letter"] in gpa_map]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def fetch_grades(opener, student_id, student_name):
    """Fetch and parse grades for a student from Genesis gradebook."""
    # Use the weekly summary URL which contains all MP grades in one page
    url = (f"https://parents.chatham-nj.org/genesis/parents"
           f"?tab1=studentdata&tab2=gradebook&tab3=weeklysummary"
           f"&studentid={student_id}&action=form")
    with opener.open(url) as resp:
        final_url = resp.url
        html = resp.read().decode("utf-8", errors="replace")
    log.info(f"Fetched grades for {student_name}: url={final_url[:80]}, len={len(html)}")
    if len(html) < 500:
        log.error(f"Response too short for {student_name} - likely redirected to login")
        return []
    # Debug: log what the notecard section actually contains
    nc_pos = html.find('notecard')
    if nc_pos >= 0:
        log.info(f"Notecard HTML snippet for {student_name}: {repr(html[nc_pos:nc_pos+300])}")
    else:
        log.warning(f"No notecard in HTML for {student_name}. Sample: {repr(html[2000:2300])}")
    return parse_grades(html, student_name)

def detect_alerts(andre_grades, arina_grades):
    alerts = []
    for c in andre_grades:
        if c["current"] is not None and c["current"] < 75:
            alerts.append(f"Andre - {c['subject']} is at {c['current']:.1f} (below 75)")
        if c["prev"] is not None and c["current"] is not None and (c["current"] - c["prev"]) <= -5:
            alerts.append(f"Andre - {c['subject']} dropped {abs(c['current']-c['prev']):.1f} pts")
    for c in arina_grades:
        if c["prev"] is not None and c["current"] is not None and (c["current"] - c["prev"]) <= -5:
            alerts.append(f"Arina - {c['subject']} dropped {abs(c['current']-c['prev']):.1f} pts")
    return alerts


def grade_badge(letter, score):
    bg, fg = GRADE_COLORS.get(letter[0], ("#eee", "#333"))
    s = f"{score:.1f}" if score is not None else "-"
    return (f'<span style="background:{bg};color:{fg};padding:2px 6px;'
            f'border-radius:3px;font-family:monospace;font-size:10px;font-weight:bold;">'
            f'{letter} {s}</span>')


def build_rows(grades):
    rows = ""
    for i, c in enumerate(grades):
        bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        badge = grade_badge(c["letter"], c["current"])
        rows += (f"<tr style='background:{bg};'>"
                 f"<td style='padding:3px 8px;border-bottom:1px solid #eee;font-size:10px;'>"
                 f"<strong style='color:#222;'>{c['subject']}</strong></td>"
                 f"<td style='padding:3px 8px;border-bottom:1px solid #eee;text-align:center;'>{badge}</td>"
                 f"</tr>")
    if not rows:
        rows = "<tr><td colspan='2' style='padding:6px;color:#aaa;font-size:10px;'>No grades available</td></tr>"
    return rows


def build_email(andre_grades, arina_grades, alerts):
    today = datetime.now().strftime("%a %b %-d, %Y")
    andre_gpa = calc_gpa(andre_grades)
    arina_gpa = calc_gpa(arina_grades)
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
    a_rows = build_rows(andre_grades)
    ar_rows = build_rows(arina_grades)
    status = "&#9888; Action Required" if alerts else "&#10003; All Good"
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>@media print {{body{{margin:0;padding:4px;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}table{{page-break-inside:avoid;}}}}</style>
</head>
<body style="margin:0;padding:6px;background:#fff;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:0 auto;">
<tr><td style="background:#1a3a6b;border-radius:3px 3px 0 0;padding:6px 10px;">
<table width="100%"><tr>
<td><span style="color:#fff;font-size:13px;font-weight:bold;">Dailerian <span style="color:#7eb8f7;">School</span> Tracker</span>
<span style="color:#a8c4e8;font-size:10px;margin-left:8px;">{today}</span></td>
<td align="right"><span style="background:#2d5a9e;color:#a8c4e8;font-size:10px;padding:2px 6px;border-radius:2px;">{status}</span></td>
</tr></table></td></tr>
<tr><td style="background:#fff;padding:6px 4px 2px 4px;">{alert_html}
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="50%" style="padding-right:3px;vertical-align:top;">
<table {ts}>
<tr><td colspan="2" style="padding:3px 8px;background:#e6f1fb;border-bottom:1px solid #ddd;">
<span style="font-size:11px;font-weight:bold;color:#0c447c;">Andre Dailerian</span>
<span style="color:#555;font-size:9px;margin-left:4px;">Gr.10 &bull; GPA {andre_gpa}</span>
</td></tr>
<tr><th {th} width="75%">Subject</th><th {th} style="text-align:center;">Grade</th></tr>
{a_rows}</table></td>
<td width="50%" style="padding-left:3px;vertical-align:top;">
<table {ts}>
<tr><td colspan="2" style="padding:3px 8px;background:#fbeaf0;border-bottom:1px solid #ddd;">
<span style="font-size:11px;font-weight:bold;color:#72243e;">Arina Dailerian</span>
<span style="color:#555;font-size:9px;margin-left:4px;">Gr.7 &bull; GPA {arina_gpa}</span>
</td></tr>
<tr><th {th} width="75%">Subject</th><th {th} style="text-align:center;">Grade</th></tr>
{ar_rows}</table></td>
</tr></table></td></tr>
<tr><td style="padding:3px;text-align:center;border-top:1px solid #eee;">
<span style="font-size:9px;color:#aaa;">Dailerian School Tracker &bull; Daily 4:00 PM &bull; Chatham School District</span>
</td></tr></table></body></html>"""


def send_email(html, alerts):
    today = datetime.now().strftime("%a %b %-d")
    flag = "Action Required" if alerts else "All Good"
    subject = f"Dailerian School Tracker - {today} - {flag}"
    payload = json.dumps({
        "personalizations": [{"to": [{"email": r} for r in EMAIL_RECIPIENTS]}],
        "from": {"email": SENDER_EMAIL, "name": "Dailerian School Tracker"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        log.info(f"Email sent! SendGrid status: {resp.status} to {len(EMAIL_RECIPIENTS)} recipients.")


def send_sms(andre_grades, alerts):
    if not TEXTBELT_KEY:
        log.warning("Textbelt key not set - skipping SMS.")
        return
    andre_gpa = calc_gpa(andre_grades)
    today = datetime.now().strftime("%a %b %-d")
    lines = [f"Tracker {today} | Andre GPA:{andre_gpa}"]
    if alerts:
        lines.append("Alerts:")
        for a in alerts:
            lines.append(f"! {a[:50]}")
    else:
        lines.append("No alerts today")
    body = "\n".join(lines)
    for phone in ANDRE_PHONES:
        data = urllib.parse.urlencode({
            "phone": phone.replace("+1", ""),
            "message": body,
            "key": TEXTBELT_KEY
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://textbelt.com/text",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            result = resp.read().decode()
            log.info(f"SMS sent to {phone}! Textbelt response: {result}")


def send_error_email(error_msg):
    """Send a plain error notification to martin@dailerian.com."""
    if not SENDGRID_API_KEY:
        log.error("Cannot send error email - no SendGrid key.")
        return
    today = datetime.now().strftime("%a %b %-d %Y %H:%M")
    payload = json.dumps({
        "personalizations": [{"to": [{"email": "martin@dailerian.com"}]}],
        "from": {"email": SENDER_EMAIL, "name": "Dailerian School Tracker"},
        "subject": f"Tracker ERROR - {today}",
        "content": [{"type": "text/plain", "value":
            f"The Dailerian School Tracker encountered an error and could not fetch grades.\n\n"
            f"Time: {today}\n"
            f"Error: {error_msg}\n\n"
            f"The daily email and SMS were NOT sent with fresh data.\n"
            f"Please check Railway logs at:\n"
            f"https://railway.com/project/6d4fb75f-68d4-471e-a157-ee63931a23b5\n\n"
            f"Common fixes:\n"
            f"- Genesis password may have changed (update GENESIS_PASS in Railway)\n"
            f"- Genesis portal may be down (try again tomorrow)\n"
            f"- Check Railway logs for full stack trace\n"
        }]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            log.info(f"Error notification sent to martin@dailerian.com (status {resp.status})")
    except Exception as e:
        log.error(f"Failed to send error notification: {e}")


def run_daily_job():
    log.info("=" * 50)
    log.info("Running Dailerian School Tracker daily job...")
    andre_grades, arina_grades = [], []
    scrape_error = None
    try:
        opener = genesis_login()
        andre_grades = fetch_grades(opener, ANDRE_ID, "Andre")
        arina_grades = fetch_grades(opener, ARINA_ID, "Arina")
        log.info(f"Grades: Andre={len(andre_grades)}, Arina={len(arina_grades)} courses")
        if len(andre_grades) == 0 and len(arina_grades) == 0:
            scrape_error = "Login succeeded but no grades were parsed. The Genesis page structure may have changed."
    except Exception as e:
        scrape_error = str(e)
        log.error(f"Genesis scrape failed: {e}")

    if scrape_error:
        log.error(f"Scraping failed - sending error notification. Error: {scrape_error}")
        send_error_email(scrape_error)
        log.info("Daily job complete (with scrape error).")
        return

    alerts = detect_alerts(andre_grades, arina_grades)
    try:
        html = build_email(andre_grades, arina_grades, alerts)
        send_email(html, alerts)
        log.info("Email complete.")
    except Exception as e:
        log.error(f"Email failed: {e}")
    try:
        send_sms(andre_grades, alerts)
        log.info("SMS complete.")
    except Exception as e:
        log.error(f"SMS failed: {e}")
    log.info("Daily job complete.")


if __name__ == "__main__":
    log.info(f"Started. Scheduled daily at {SEND_TIME}.")
    run_daily_job()  # TEST RUN - will disable after
    schedule.every().day.at(SEND_TIME).do(run_daily_job)
    while True:
        schedule.run_pending()
        time.sleep(30)
