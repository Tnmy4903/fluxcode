"""
Requirements Module API
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.db.schemas import (
    RequirementCreate,
    RequirementUpdate,
    RequirementOut,
    RequirementApprovalRequest
)
from app.services.service_layer import RequirementService, ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

requirement_router = APIRouter()
requirement_service = RequirementService()
activity_service = ActivityLogService()


@requirement_router.post("/requirements", response_model=dict)
async def create_requirement(req: RequirementCreate, current_user: dict = Depends(get_current_user)):
    """Create requirement documentation (Admins only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can create requirements")
        
        req_dict = req.dict()
        result = await requirement_service.create_requirement(
            created_by=current_user["id"],
            **req_dict
        )
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Requirement Created", "Requirement", result["id"]
        )
        
        logger_project.info(f"Requirement created: {result['id']} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@requirement_router.get("/requirements/{requirement_id}", response_model=dict)
async def get_requirement(requirement_id: str, current_user: dict = Depends(get_current_user)):
    """Get requirement details"""
    try:
        req = await requirement_service.req_repo.find_by_id(requirement_id)
        if not req:
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        req["id"] = str(req["_id"])
        return req
    except Exception as e:
        raise exception_to_http(e)


@requirement_router.put("/requirements/{requirement_id}", response_model=dict)
async def update_requirement(requirement_id: str, updates: RequirementUpdate, current_user: dict = Depends(get_current_user)):
    """Update requirement"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can update requirements")
        
        update_dict = updates.dict(exclude_unset=True)
        result = await requirement_service.update_requirement(
            requirement_id=requirement_id,
            updated_by=current_user["id"],
            **update_dict
        )
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Requirement Updated", "Requirement", requirement_id,
            {"updates": update_dict}
        )
        
        logger_project.info(f"Requirement updated: {requirement_id} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)
    
@requirement_router.patch("/requirements/{requirement_id}/approve", response_model=dict)
async def approve_requirement(
    requirement_id: str,
    payload: RequirementApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Approve requirement (Super Admin only)"""
    try:

        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can approve requirements"
            )

        result = await requirement_service.approve_requirement(
            requirement_id=requirement_id,
            approved_by=current_user["id"],
            remarks=payload.remarks
        )

        await activity_service.log_activity(
            current_user["id"],
            current_user["role"],
            "Requirement Approved",
            "Requirement",
            requirement_id
        )

        logger_project.info(
            f"Requirement approved: {requirement_id} by {current_user['email']}"
        )

        return result

    except Exception as e:
        raise exception_to_http(e)

@requirement_router.patch("/requirements/{requirement_id}/request-changes", response_model=dict)
async def request_requirement_changes(
    requirement_id: str,
    payload: RequirementApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request requirement changes (Super Admin only)"""
    try:

        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can request changes"
            )

        result = await requirement_service.request_changes(
            requirement_id=requirement_id,
            remarks=payload.remarks
        )

        await activity_service.log_activity(
            current_user["id"],
            current_user["role"],
            "Requirement Changes Requested",
            "Requirement",
            requirement_id
        )

        logger_project.info(
            f"Requirement changes requested: {requirement_id}"
        )

        return result

    except Exception as e:
        raise exception_to_http(e)

@requirement_router.delete("/requirements/{requirement_id}", response_model=dict)
async def delete_requirement(requirement_id: str, current_user: dict = Depends(get_current_user)):
    """Delete requirement"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can delete requirements")
        
        deleted = await requirement_service.req_repo.delete(requirement_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Requirement Deleted", "Requirement", requirement_id
        )
        
        return {"message": "Requirement deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)


@requirement_router.get("/leads/{lead_id}/requirements", response_model=dict)
async def get_lead_requirements(lead_id: str, current_user: dict = Depends(get_current_user)):
    """Get requirements for lead"""
    try:
        req = await requirement_service.req_repo.find_by_lead(lead_id)
        if not req:
            raise HTTPException(status_code=404, detail="No requirements found for this lead")
        
        req["id"] = str(req["_id"])
        return req
    except Exception as e:
        raise exception_to_http(e)


@requirement_router.get("/projects/{project_id}/requirements", response_model=dict)
async def get_project_requirements(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get requirements for project"""
    try:
        req = await requirement_service.req_repo.find_by_project(project_id)
        if not req:
            raise HTTPException(status_code=404, detail="No requirements found for this project")
        
        req["id"] = str(req["_id"])
        return req
    except Exception as e:
        raise exception_to_http(e)
