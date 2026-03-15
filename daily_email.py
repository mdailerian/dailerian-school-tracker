#!/usr/bin/env python3
"""
Dailerian School Tracker — Daily Email Notifier
Runs every day at 4:00 PM, pulls live data from Genesis and Schoology,
and sends a formatted HTML summary to all recipients.
"""

import smtplib
import schedule
import time
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

GMAIL_SENDER    = "martin.dailerian@gmail.com"
GMAIL_APP_PASS  = "rmep fexi gqhv lopd"

RECIPIENTS = [
    "andredailerian37@gmail.com",
    "andredailerian@chatham-nj.org",
    "monika.a.grabania@gmail.com",
    "Monika.Grabania@vitaminshoppe.com",
    "martin.dailerian@jpmchase.com",
    "arinadailerian@chatham-nj.org",
]
