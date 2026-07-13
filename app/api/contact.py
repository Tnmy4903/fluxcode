from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from app.db.database import db
from app.db.schemas import (
    ContactFormCreate, ContactFormOut,
    NewsletterSignup, NewsletterOut
)
from app.services.email import send_contact_alert

contact_router = APIRouter()


# ───────────────────────────────
# 📰 Newsletter Signup
# ───────────────────────────────
@contact_router.post("/newsletter", response_model=NewsletterOut)
async def signup_newsletter(payload: NewsletterSignup):
    existing = await db.newsletter.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Already subscribed")

    doc = {
        "email": payload.email,
        "subscribedAt": datetime.utcnow()
    }
    result = await db.newsletter.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return NewsletterOut(**doc)


# ───────────────────────────────
# 📩 Contact Form Submission + Alert
# ───────────────────────────────
@contact_router.post("/contact", response_model=ContactFormOut)
async def submit_contact_form(form: ContactFormCreate):
    doc = {
        "name": form.name,
        "email": form.email,
        "message": form.message,
        "submittedAt": datetime.utcnow()
    }
    result = await db.contact_forms.insert_one(doc)
    doc["id"] = str(result.inserted_id)

    # ✅ Send email alert
    send_contact_alert(form.name, form.email, form.message)

    return ContactFormOut(**doc)

