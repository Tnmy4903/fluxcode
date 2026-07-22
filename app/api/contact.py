"""
Contact Form API
"""

from fastapi import APIRouter

from app.db.schemas import (
    ContactFormCreate,
    ContactFormOut
)
from app.exceptions import exception_to_http
from app.services.service_layer import ContactService


contact_router = APIRouter()

contact_service = ContactService()


@contact_router.post(
    "/contact",
    response_model=ContactFormOut
)
async def submit_contact_form(
    form: ContactFormCreate
):
    """Submit contact form"""

    try:
        return await contact_service.submit_contact_form(
            name=form.name,
            email=form.email,
            message=form.message
        )

    except Exception as e:
        raise exception_to_http(e)