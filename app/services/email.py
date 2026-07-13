import os
import requests
from dotenv import load_dotenv
from typing import Optional
from fastapi import UploadFile

load_dotenv()

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
ALERT_RECEIVER_EMAIL = os.getenv("ALERT_RECEIVER_EMAIL")


def send_contact_alert(name: str, email: str, message: str) -> None:
    if not all([MAILGUN_API_KEY, MAILGUN_DOMAIN, ALERT_RECEIVER_EMAIL]):
        raise Exception("Missing Mailgun configuration")

    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"FluxCode <postmaster@{MAILGUN_DOMAIN}>",
            "to": ALERT_RECEIVER_EMAIL,
            "subject": f"📩 New Contact Form Submission from {name}",
            "text": f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        }
    )

    if response.status_code != 200:
        raise Exception("Failed to send email alert")


def send_mass_email(subject: str, body: str, recipients: list[str], attachment: Optional[UploadFile] = None):
    if not all([MAILGUN_API_KEY, MAILGUN_DOMAIN]):
        raise Exception("Missing Mailgun config")

    files = []
    if attachment:
        files = [("attachment", (attachment.filename, attachment.file.read()))]

    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=files,
        data={
            "from": f"Fluxcode Newsletter <postmaster@{MAILGUN_DOMAIN}>",
            "to": recipients,
            "subject": subject,
            "text": body
        }
    )


def send_invoice_email(to_email: str, subject: str, body: str, file_path: str):
    if not all([MAILGUN_API_KEY, MAILGUN_DOMAIN]):
        raise Exception("Missing Mailgun config")

    with open(file_path, "rb") as f:
        files = [("attachment", (os.path.basename(file_path), f.read()))]

    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files=files,
        data={
            "from": f"Invoicing <postmaster@{MAILGUN_DOMAIN}>",
            "to": to_email,
            "subject": subject,
            "text": body
        }
    )
