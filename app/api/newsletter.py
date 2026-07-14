from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from app.api.auth import get_current_user
from app.db.database import db
from app.services.email import send_mass_email
from app.db.schemas import NewsletterSendOut

newsletter_router = APIRouter()


# ──────────────────────────────────────────────────
# 📧 Admin Newsletter Broadcast to Subscribers (Super Admin Only)
# ──────────────────────────────────────────────────
@newsletter_router.post("/send", response_model=NewsletterSendOut)
async def send_newsletter(
    subject: str = Form(...),
    body: str = Form(...),
    file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    # Only super_admin can send newsletters
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can send newsletters")

    cursor = db.newsletter.find()
    recipients = [entry["email"] async for entry in cursor]

    if not recipients:
        raise HTTPException(status_code=404, detail="No newsletter subscribers")

    response = send_mass_email(subject, body, recipients, file)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Email sending failed")

    return NewsletterSendOut(
        sentTo=len(recipients),
        subject=subject,
        status="Sent"
    )
