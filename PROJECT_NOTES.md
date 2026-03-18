# Dailerian School Tracker - Project Notes
Last updated: March 17, 2026

## What This Is
A fully automated daily notification system that sends:
- Email (HTML, print-friendly) to 7 family recipients at 4:00 PM every day
- SMS to 3 phone numbers with Andre's GPA + assignments due in the next 3 days

Data is hardcoded from Chatham School District portals (Genesis + Schoology).
Future enhancement: live scraping.

## Architecture
GitHub (code) -> Railway (runs 24/7) -> SendGrid (email) + Textbelt (SMS)
- Language: Python 3.11
- Scheduler: schedule library - fires daily at 16:00
- On startup: runs job immediately, then waits for 4:00 PM schedule
- Server region: us-east4 (required for Textbelt North America keys)

## Repository
GitHub: https://github.com/mdailerian/dailerian-school-tracker
- Account: mdailerian (martin@dailerian.com)
- Files: daily_email.py, requirements.txt, Procfile, runtime.txt

## Deployment
Railway: https://railway.com/project/6d4fb75f-68d4-471e-a157-ee63931a23b5
- Service: worker
- Service ID: 0e3bbac8-c2f4-428d-bd91-5d2d3c2c9751
- Region: us-east4 (must stay US for Textbelt to work)
- Auto-deploys on every GitHub push

## Environment Variables (Railway)
All secrets live in Railway only - never in GitHub.

| Variable | Purpose |
|----------|---------|
| SENDGRID_API_KEY | SendGrid email API key |
| GMAIL_SENDER | martin.dailerian@gmail.com (verified sender) |
| GMAIL_APP_PASS | Gmail app password (legacy, no longer used) |
| TEXTBELT_KEY | Textbelt SMS API key (~100 texts purchased) |
| ANDRE_PHONE | Primary test phone: +16462442292 |
| TWILIO_ACCOUNT_SID | Legacy Twilio (not used, can delete) |
| TWILIO_AUTH_TOKEN | Legacy Twilio (not used, can delete) |
| TWILIO_FROM_NUMBER | Legacy Twilio (not used, can delete) |

## Email Recipients (7)
1. andredailerian37@gmail.com
2. andredailerian@chatham-nj.org  -- PENDING IT whitelist
3. monika.a.grabania@gmail.com
4. Monika.Grabania@vitaminshoppe.com
5. martin.dailerian@jpmchase.com
6. arinadailerian@chatham-nj.org  -- PENDING IT whitelist
7. martin@dailerian.com

Note: Email sent to Dr. Michael LaSusa (mlasusa@chatham-nj.org, 973-457-2500) to whitelist sender.

## SMS Recipients (3)
1. +16462442292 - test/Martin number
2. +19085147364 - Andre's phone
3. +16462442253 - additional recipient

To update Andre's phone: change ANDRE_PHONE in Railway Variables.
To add/remove numbers: edit ANDRE_PHONES list in daily_email.py.

## Student Data

### Andre Dailerian - Grade 10, Chatham HS
- Student ID: 20286810
- Genesis login: parent account (martin@dailerian.com)
- Schoology: andredailerian@chatham-nj.org

Current Grades (MP2):
| Subject | Teacher | Grade |
|---------|---------|-------|
| Honors English 10 | Agelis, Nicholas | B 83.3 |
| US History 2A | Nagy, Brian | D 69.3 ALERT |
| Spanish 3 | Fix, Marlin | A 90.6 |
| Chemistry A (lab) | Naumova, Yelena | B 82.1 |
| Algebra 2A | Cordano, Dagmar | C 77.6 |
| Experiencing Fine Art | Hull, Candace | A 94.7 |
| Health / PE / Driver Ed | Picariello, Evan | A 100.0 |
| GPA | | 2.97 |

### Arina Dailerian - Grade 7, Chatham MS
- Student ID: 20316811

Current Grades (MP3):
| Subject | Teacher | Grade |
|---------|---------|-------|
| Band 7 | Spriggs, Christie | A 95.9 |
| Dream Room Design Lab | Hitchings, James | A 96.9 |
| English 7 Honors | Iannuzzi, George | B 81.4 |
| Health 7 | Nydegger, Kelly | A 92.5 |
| Mathematics Honors 7 | Novick, Amanda | B 80.0 |
| Physical Education 7 | Murphy, Liam | A 100.0 |
| Science 7 | LoPorto, Lauren | B 85.8 |
| World Cultures & Geography | Becker, Carly | A 93.8 |
| French 7 | Engell, Tine | A 90.7 |
| GPA | | 3.79 |

## Services & Costs
| Service | Purpose | Cost | Account |
|---------|---------|------|---------|
| GitHub | Code storage | Free | mdailerian |
| Railway | 24/7 hosting | Free ($5/mo credit) | martin@dailerian.com |
| SendGrid | Email delivery | Free (100/day) | martin@dailerian.com |
| Textbelt | SMS delivery | ~$9/100 texts | Key in Railway |
| Twilio | SMS (abandoned) | Paid but unused | martin@dailerian.com |

## How to Update Grades / Assignments
Open daily_email.py in GitHub and update:
- ANDRE_GRADES = [ ... ]       # Andre's subjects, teachers, grades
- ARINA_GRADES = [ ... ]       # Arina's subjects, teachers, grades
- ANDRE_ASSIGNMENTS = {
    "overdue": [ ... ],        # Overdue assignments
    "upcoming": [ ... ],       # Upcoming with due dates like "Mon 3/16"
  }
Commit -> Railway auto-redeploys within 2 minutes.

## Alert Logic
Alerts appear in the email header (yellow box) when:
- Any of Andre's grades drops below 75
- Any grade drops 5+ points from previous marking period
- Any assignment is overdue (within last 2 weeks)

## SMS Format
Single segment (<160 chars) to avoid carrier garbling:
  Tracker Mon Mar 17 | Andre GPA:2.97
  Due 3 days:
  * OVERDUE - HIST: Voice From My Lai
  * Mo CHEM: pkt p.3,6-7
  * Mo ALG: Test CH 5 Part 2
  * Tu CHEM: Finish lab analysis
  * Tu ENG: Read ch.12

Subject abbreviations: ENG, HIST, SPA, CHEM, ALG, ART, PE

## Known Issues / TODO
1. SMS formatting - some assignment titles still garble on certain carriers
2. Arina's assignments - not connected (Schoology login not yet provided)
3. Live data scraping - grades/assignments are hardcoded, not auto-scraped
4. Textbelt quota - ~20 texts remaining as of Mar 17, buy more at textbelt.com

## How to Resume This Project
Start a new Claude conversation and say:
  "I have a school tracker project called Dailerian School Tracker.
   GitHub: github.com/mdailerian/dailerian-school-tracker
   Railway project ID: 6d4fb75f-68d4-471e-a157-ee63931a23b5
   See PROJECT_NOTES.md in the repo for full details."

## Security Notes
- NEVER paste API keys in Claude chat - GitHub secret scanning auto-revokes them
- All secrets stored in Railway environment variables only
- GitHub token should be revoked at github.com/settings/tokens
- Passwords to change: Genesis (martin@dailerian.com), GitHub (mdailerian)
