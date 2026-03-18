# Dailerian School Tracker - Project Notes
Last updated: March 17, 2026

---

## What This Is
A fully automated daily notification system that:
- Logs into the Chatham Genesis parent portal at 4:00 PM every day
- Scrapes live grades for Andre and Arina
- Sends a formatted HTML email to 7 family recipients
- Sends an SMS summary to 3 phone numbers with Andre's GPA and any alerts

No grades or assignments are hardcoded. All data is fetched live from Genesis on every run.

---

## Architecture
Genesis (live scrape) -> Email (SendGrid) + SMS (Textbelt)
All running on Railway (us-east4), triggered by GitHub push, scheduled at 16:00 daily.

- Language: Python 3.11
- Scheduler: schedule library - fires daily at 16:00
- On startup: runs job immediately, then waits for 4:00 PM
- Server region: us-east4 (REQUIRED - Textbelt North America keys only work from US servers)

---

## Repository
GitHub: https://github.com/mdailerian/dailerian-school-tracker
- Account: mdailerian (martin@dailerian.com)
- Main file: daily_email.py
- Also: requirements.txt, Procfile, runtime.txt, PROJECT_NOTES.md

---

## Deployment
Railway: https://railway.com/project/6d4fb75f-68d4-471e-a157-ee63931a23b5
- Service: worker
- Service ID: 0e3bbac8-c2f4-428d-bd91-5d2d3c2c9751
- Region: us-east4 (do NOT change - Textbelt will fail from non-US regions)
- Auto-deploys on every GitHub push

---

## Environment Variables (Railway)
ALL secrets and credentials live in Railway only - never in GitHub or this document.

| Variable | Purpose | Notes |
|----------|---------|-------|
| SENDGRID_API_KEY | SendGrid email API key | Never paste in chat - GitHub auto-revokes |
| GMAIL_SENDER | Sender email address | martin.dailerian@gmail.com |
| GMAIL_APP_PASS | Legacy Gmail password | No longer used for sending |
| TEXTBELT_KEY | Textbelt SMS API key | ~5 texts remaining Mar 17 - buy more |
| ANDRE_PHONE | Primary SMS recipient | +16462442292 (test/Martin number) |
| GENESIS_USER | Genesis parent login email | martin@dailerian.com |
| GENESIS_PASS | Genesis parent login password | Set directly in Railway, never share |
| TWILIO_ACCOUNT_SID | Legacy Twilio | Not used, safe to delete |
| TWILIO_AUTH_TOKEN | Legacy Twilio | Not used, safe to delete |
| TWILIO_FROM_NUMBER | Legacy Twilio | Not used, safe to delete |

---

## How the Scraper Works

### Login
1. GET the Genesis login page to pick up pre-login cookies
2. POST credentials to: https://parents.chatham-nj.org/genesis/sis/j_security_check?parents=Y
3. Fields: j_username, j_password, idTokenString (empty)
4. Session maintained via cookie jar throughout the run

### Grade Scraping
- Andre (student ID: 20286810): gradebook page via Genesis parents portal
- Arina (student ID: 20316811): same URL pattern with her student ID
- The grades page contains a table with class "notecard" containing span elements
- Span pattern: [term] | [subject name] [grade1] [grade2] [grade3] ...
  - term = FY, S1, S2, Q1, Q2, Q3, Q4
  - grades are floats like 83.40, or "---" for empty marking periods
  - Current grade = last non-null grade value
  - Previous grade = second-to-last non-null grade value (for drop detection)
- GPA is calculated dynamically from scraped grades (4.0 scale)

### Error Handling
If Genesis scrape fails OR returns 0 courses:
- Normal email and SMS are NOT sent
- A plain-text error notification is sent to martin@dailerian.com only
- Error email includes: error message, timestamp, Railway logs link, common fixes

Common scrape failure causes:
- Genesis password changed (update GENESIS_PASS in Railway)
- Genesis portal is down
- Session redirect / login cookies not accepted
- HTML structure of the grades page changed

---

## Email Recipients (7)
1. andredailerian37@gmail.com
2. andredailerian@chatham-nj.org  -- PENDING: school IT whitelist
3. monika.a.grabania@gmail.com
4. Monika.Grabania@vitaminshoppe.com
5. martin.dailerian@jpmchase.com
6. arinadailerian@chatham-nj.org  -- PENDING: school IT whitelist
7. martin@dailerian.com

Contact for whitelist: Dr. Michael LaSusa (mlasusa@chatham-nj.org, 973-457-2500)

---

## SMS Recipients (3)
Hardcoded in daily_email.py ANDRE_PHONES list:
1. ANDRE_PHONE env var (default: +16462442292) - test/Martin number
2. +19085147364 - Andre's phone
3. +16462442253 - additional recipient

To add/remove numbers: edit ANDRE_PHONES list in daily_email.py and commit.
To change primary: update ANDRE_PHONE in Railway Variables.

SMS content: Andre's GPA + any alerts. If no alerts: "No alerts today".

---

## Student Info
- Andre Dailerian: Grade 10, Chatham HS, Student ID 20286810
- Arina Dailerian: Grade 7, Chatham MS, Student ID 20316811
- Grades are NOT stored in code - fetched live from Genesis every run

---

## Alert Logic
Alerts trigger when (evaluated against live scraped data):
- Any of Andre's grades drops below 75
- Any grade drops 5+ points from previous marking period (either student)

Alerts appear in the email header (yellow box) and SMS message.

---

## Email Format
- Compact 2-column layout (Andre left, Arina right)
- Print-friendly with media print CSS
- Color-coded grade badges: A=green, B=blue, C=amber, D=red
- Live GPA calculated from scraped grades
- Subject and current grade shown for all courses

---

## Hardcoded Values Audit (as of Mar 17, 2026)
The only values NOT in Railway env vars:
- Student IDs: 20286810 (Andre), 20316811 (Arina) - not sensitive
- SMS phone numbers: +19085147364, +16462442253 - move to env vars if needed
- Email recipients list - hardcoded in script, not sensitive
- Subject abbreviation map - static lookup table, not sensitive
- Fallback sender email: martin.dailerian@gmail.com (Railway var takes precedence)
- Fallback Genesis user: martin@dailerian.com (Railway var takes precedence)

NO grades, GPAs, assignments, passwords, or API keys are hardcoded.

---

## Services & Costs
| Service | Purpose | Cost | Account |
|---------|---------|------|---------|
| GitHub | Code storage | Free | mdailerian |
| Railway | 24/7 hosting | Free ($5/mo credit) | martin@dailerian.com |
| SendGrid | Email delivery | Free (100/day) | martin@dailerian.com |
| Textbelt | SMS delivery | ~$9/100 texts (~5 remaining) | Key in Railway |
| Twilio | SMS (abandoned) | Paid but unused | martin@dailerian.com |

---

## How to Resume This Project
Start a new Claude conversation and say:

  "I have a school tracker project called Dailerian School Tracker.
   GitHub: github.com/mdailerian/dailerian-school-tracker
   Railway project ID: 6d4fb75f-68d4-471e-a157-ee63931a23b5
   See PROJECT_NOTES.md in the repo for full details."

---

## Known Issues / TODO
1. Genesis scraping returns 0 grades - login works but HTML parser needs fixing
   - Error notification email sent to martin@dailerian.com when this happens
   - Debug: check Railway logs for HTML snippet to identify correct CSS class/structure

2. Assignments not yet scraped from Schoology
   - Email shows grades only (no due dates)
   - Schoology requires separate login for Andre

3. Textbelt quota low (~5 texts remaining as of Mar 17) - buy more at textbelt.com

---

## Security Notes
- NEVER paste API keys or passwords in Claude chat
  GitHub secret scanning auto-revokes keys immediately upon detection
- All secrets stored in Railway environment variables only
- Revoke the GitHub personal access token used during build at github.com/settings/tokens
- Change passwords: Genesis portal (martin@dailerian.com), GitHub account (mdailerian)
