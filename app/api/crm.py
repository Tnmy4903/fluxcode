"""
CRM/Lead Management API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from app.db.schemas import LeadCreate, LeadUpdate, LeadOut
from app.services.service_layer import LeadService, ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

lead_router = APIRouter()
lead_service = LeadService()
activity_service = ActivityLogService()


@lead_router.post("/leads", response_model=dict)
async def create_lead(lead: LeadCreate, current_user: dict = Depends(get_current_user)):
    """Create new lead (Super Admin or Sub Admin only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can create leads")
        
        result = await lead_service.create_lead(
            company_name=lead.companyName,
            contact_person=lead.contactPerson,
            phone=lead.phone,
            email=lead.email,
            business=lead.business,
            lead_source=lead.leadSource,
            notes=lead.notes
        )
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Lead Created", "Lead", result["id"]
        )
        
        logger_project.info(f"Lead created: {result['id']} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@lead_router.get("/leads", response_model=List[dict])
async def get_all_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    stage: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all leads (Super Admin or Sub Admin only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can view leads")
        
        if stage:
            leads = await lead_service.lead_repo.find_by_stage(stage, skip, limit)
        else:
            leads = await lead_service.lead_repo.get_all_sorted(skip, limit)
        
        for lead in leads:
            lead["id"] = str(lead["_id"])
        
        return leads
    except Exception as e:
        raise exception_to_http(e)


@lead_router.get("/leads/{lead_id}", response_model=dict)
async def get_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    """Get lead details"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can view leads")
        
        lead = await lead_service.lead_repo.find_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead["id"] = str(lead["_id"])
        return lead
    except Exception as e:
        raise exception_to_http(e)


@lead_router.put("/leads/{lead_id}", response_model=dict)
async def update_lead(lead_id: str, updates: LeadUpdate, current_user: dict = Depends(get_current_user)):
    """Update lead"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can update leads")
        
        update_dict = updates.dict(exclude_unset=True)
        result = await lead_service.update_lead(lead_id, current_user["id"], current_user["role"], **update_dict)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Lead Updated", "Lead", lead_id,
            {"updates": update_dict}
        )
        
        logger_project.info(f"Lead updated: {lead_id} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@lead_router.post("/leads/{lead_id}/assign/{sub_admin_id}", response_model=dict)
async def assign_lead(lead_id: str, sub_admin_id: str, current_user: dict = Depends(get_current_user)):
    """Assign lead to sub-admin (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can assign leads")
        
        result = await lead_service.assign_lead(lead_id, sub_admin_id)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Lead Assigned", "Lead", lead_id,
            {"assignedTo": sub_admin_id}
        )
        
        return result
    except Exception as e:
        raise exception_to_http(e)


@lead_router.get("/leads/{lead_id}/history", response_model=List[dict])
async def get_lead_history(lead_id: str, current_user: dict = Depends(get_current_user)):
    """Get lead change history"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can view lead history")
        
        lead = await lead_service.lead_repo.find_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return lead.get("history", [])
    except Exception as e:
        raise exception_to_http(e)
