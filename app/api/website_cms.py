"""
Website CMS API
"""

from typing import Dict, List

from backend.app.db.schemas import WebsiteContentOut
from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.exceptions import exception_to_http
from app.services.service_layer import WebsiteCMSService


website_cms_router = APIRouter()

website_service = WebsiteCMSService()


@website_cms_router.put(
    "/website/sections/{section}",
    response_model=WebsiteContentOut
)
async def update_website_section(
    section: str,
    content: Dict,
    current_user: dict = Depends(get_current_user)
):
    """Create or update website section"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can manage website content"
            )

        return await website_service.update_section(
            section=section,
            content=content,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get(
    "/website/sections/{section}",
    response_model=WebsiteContentOut
)
async def get_website_section(
    section: str
):
    """Get website section"""

    try:
        return await website_service.get_section(
            section
        )

    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get(
    "/website/sections",
    response_model=List[WebsiteContentOut]
)
async def get_all_website_sections():
    """Get all website sections"""

    try:
        return await website_service.get_all_sections()

    except Exception as e:
        raise exception_to_http(e)