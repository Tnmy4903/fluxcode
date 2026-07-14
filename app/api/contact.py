from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.db.database import db
from app.db.schemas import (
    ContactFormCreate, ContactFormOut,
    NewsletterSignup, NewsletterOut
)
from app.services.service_layer import ContactService
from app.exceptions import exception_to_http

contact_router = APIRouter()
contact_service = ContactService()


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
    try:
        result = await contact_service.submit_contact_form(
            name=form.name,
            email=form.email,
            message=form.message
        )

        return ContactFormOut(**result)

    except Exception as exc:
        raise exception_to_http(exc)

