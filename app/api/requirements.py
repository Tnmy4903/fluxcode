"""
Requirements Module API
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.db.schemas import (
    RequirementCreate,
    RequirementUpdate,
    RequirementOut,
    RequirementApprovalRequest
)
from app.exceptions import exception_to_http
from app.services.service_layer import RequirementService


requirement_router = APIRouter()

requirement_service = RequirementService()


@requirement_router.post(
    "/requirements",
    response_model=RequirementOut
)
async def create_requirement(
    req: RequirementCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create requirement"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can create requirements"
            )

        return await requirement_service.create_requirement(
            current_user=current_user,
            created_by=current_user["id"],
            **req.dict()
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.get(
    "/requirements/{requirement_id}",
    response_model=RequirementOut
)
async def get_requirement(
    requirement_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get requirement"""

    try:
        return await requirement_service.get_requirement(
            requirement_id
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.put(
    "/requirements/{requirement_id}",
    response_model=RequirementOut
)
async def update_requirement(
    requirement_id: str,
    updates: RequirementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update requirement"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can update requirements"
            )

        return await requirement_service.update_requirement(
            requirement_id=requirement_id,
            current_user=current_user,
            updated_by=current_user["id"],
            **updates.dict(exclude_unset=True)
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.patch(
    "/requirements/{requirement_id}/approve",
    response_model=RequirementOut
)
async def approve_requirement(
    requirement_id: str,
    payload: RequirementApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Approve requirement"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can approve requirements"
            )

        return await requirement_service.approve_requirement(
            requirement_id=requirement_id,
            current_user=current_user,
            approved_by=current_user["id"],
            remarks=payload.remarks
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.patch(
    "/requirements/{requirement_id}/request-changes",
    response_model=RequirementOut
)
async def request_requirement_changes(
    requirement_id: str,
    payload: RequirementApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Request requirement changes"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can request changes"
            )

        return await requirement_service.request_changes(
            requirement_id=requirement_id,
            current_user=current_user,
            remarks=payload.remarks
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.delete(
    "/requirements/{requirement_id}",
    response_model=dict
)
async def delete_requirement(
    requirement_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete requirement"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can delete requirements"
            )

        return await requirement_service.delete_requirement(
            requirement_id=requirement_id,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.get(
    "/leads/{lead_id}/requirements",
    response_model=RequirementOut
)
async def get_lead_requirements(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get lead requirements"""

    try:
        return await requirement_service.get_lead_requirements(
            lead_id
        )

    except Exception as e:
        raise exception_to_http(e)


@requirement_router.get(
    "/projects/{project_id}/requirements",
    response_model=RequirementOut
)
async def get_project_requirements(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get project requirements"""

    try:
        return await requirement_service.get_project_requirements(
            project_id
        )

    except Exception as e:
        raise exception_to_http(e)