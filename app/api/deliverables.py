"""
Deliverables Management API
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.db.schemas import DeliverablesCreate, DeliverablesOut, DeliverablesUpdate
from app.exceptions import exception_to_http
from app.services.service_layer import DeliverablesService


deliverables_router = APIRouter()

deliverables_service = DeliverablesService()


@deliverables_router.post(
    "/projects/{project_id}/deliverables",
    response_model=DeliverablesOut
)
async def create_deliverables(
    project_id: str,
    deliverables: DeliverablesCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create project deliverables"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can create deliverables"
            )

        return await deliverables_service.create_deliverables(
            project_id=project_id,
            current_user=current_user,
            **deliverables.dict()
        )

    except Exception as e:
        raise exception_to_http(e)


@deliverables_router.get(
    "/projects/{project_id}/deliverables",
    response_model=DeliverablesOut
)
async def get_deliverables(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get project deliverables"""

    try:
        return await deliverables_service.get_deliverables(
            project_id=project_id,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)


@deliverables_router.put(
    "/projects/{project_id}/deliverables",
    response_model=DeliverablesOut
)
async def update_deliverables(
    project_id: str,
    updates: DeliverablesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update project deliverables"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can update deliverables"
            )

        return await deliverables_service.update_deliverables(
            project_id=project_id,
            current_user=current_user,
            **updates.dict(exclude_unset=True)
        )

    except Exception as e:
        raise exception_to_http(e)


@deliverables_router.delete(
    "/projects/{project_id}/deliverables",
    response_model=dict
)
async def delete_deliverables(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete project deliverables"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can delete deliverables"
            )

        return await deliverables_service.delete_deliverables(
            project_id=project_id,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)