"""
CRM/Lead Management API
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.db.schemas import LeadCreate, LeadUpdate, LeadOut, LeadHistoryEvent, LeadStage
from app.exceptions import exception_to_http
from app.services.service_layer import LeadService


lead_router = APIRouter()

lead_service = LeadService()


@lead_router.post(
    "/leads",
    response_model=LeadOut
)
async def create_lead(
    lead: LeadCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new lead"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can create leads"
            )

        return await lead_service.create_lead(
            current_user=current_user,
            company_name=lead.companyName,
            contact_person=lead.contactPerson,
            phone=lead.phone,
            email=lead.email,
            business=lead.business,
            lead_source=lead.leadSource,
            notes=lead.notes
        )

    except Exception as e:
        raise exception_to_http(e)


@lead_router.get(
    "/leads",
    response_model=List[LeadOut]
)
async def get_all_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    stage: LeadStage | None = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all leads"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can view leads"
            )

        return await lead_service.get_all_leads(
            skip=skip,
            limit=limit,
            stage=stage
        )

    except Exception as e:
        raise exception_to_http(e)


@lead_router.get("/leads/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get lead details"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can view leads"
            )

        return await lead_service.get_lead(
            lead_id
        )

    except Exception as e:
        raise exception_to_http(e)


@lead_router.put(
    "/leads/{lead_id}",
    response_model=LeadOut
)
async def update_lead(
    lead_id: str,
    updates: LeadUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update lead"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can update leads"
            )

        return await lead_service.update_lead(
            lead_id=lead_id,
            current_user=current_user,
            updated_by=current_user["id"],
            **updates.dict(exclude_unset=True)
        )

    except Exception as e:
        raise exception_to_http(e)


@lead_router.post(
    "/leads/{lead_id}/assign/{sub_admin_id}",
    response_model=LeadOut
)
async def assign_lead(
    lead_id: str,
    sub_admin_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign lead to sub-admin"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can assign leads"
            )

        return await lead_service.assign_lead(
            lead_id=lead_id,
            sub_admin_id=sub_admin_id,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)


@lead_router.get(
    "/leads/{lead_id}/history",
    response_model=List[LeadHistoryEvent]
)
async def get_lead_history(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get lead history"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can view lead history"
            )

        return await lead_service.get_lead_history(
            lead_id
        )

    except Exception as e:
        raise exception_to_http(e)
