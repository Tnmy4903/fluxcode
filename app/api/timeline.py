"""
Project Timeline API
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.db.schemas import TimelineEventCreate, TimelineEventOut
from app.exceptions import exception_to_http
from app.services.service_layer import TimelineService


timeline_router = APIRouter()

timeline_service = TimelineService()


@timeline_router.post(
    "/projects/{project_id}/timeline",
    response_model=TimelineEventOut
)
async def add_timeline_event(
    project_id: str,
    event: TimelineEventCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add timeline event (Admins only)"""

    try:

        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can add timeline events"
            )

        return await timeline_service.add_timeline_event(
            project_id=project_id,
            title=event.title,
            description=event.description,
            created_by=current_user["id"]
        )

    except Exception as e:
        raise exception_to_http(e)


@timeline_router.get(
    "/projects/{project_id}/timeline",
    response_model=list[TimelineEventOut]
)
async def get_project_timeline(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get project timeline"""

    try:

        return await timeline_service.get_project_timeline(
            project_id=project_id,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise exception_to_http(e)


@timeline_router.delete(
    "/timeline/{event_id}",
    response_model=dict
)
async def delete_timeline_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete timeline event (Super Admin only)"""

    try:

        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can delete timeline events"
            )

        return await timeline_service.delete_timeline_event(
            event_id,
            current_user
        )

    except Exception as e:
        raise exception_to_http(e)