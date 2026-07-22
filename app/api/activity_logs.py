"""
Activity Logs API
"""

from typing import List

from backend.app.db.schemas import ActivityLogOut
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.exceptions import exception_to_http
from app.services.service_layer import ActivityLogService


activity_router = APIRouter()

activity_service = ActivityLogService()


@activity_router.get(
    "/activity-logs",
    response_model=List[ActivityLogOut]
)
async def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can view activity logs"
            )

        return await activity_service.get_all_logs(
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise exception_to_http(e)


@activity_router.get(
    "/activity-logs/user/{user_id}",
    response_model=List[ActivityLogOut]
)
async def get_user_activity_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs for a user"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can view user activity"
            )

        return await activity_service.get_user_activity_logs(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise exception_to_http(e)


@activity_router.get(
    "/activity-logs/entity/{entity_id}",
    response_model=List[ActivityLogOut]
)
async def get_entity_activity(
    entity_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get activity history for entity"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can view activity logs"
            )

        return await activity_service.get_entity_history(
            entity_id=entity_id,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise exception_to_http(e)


@activity_router.get(
    "/activity-logs/{log_id}",
    response_model=ActivityLogOut
)
async def get_activity_log(
    log_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get activity log"""

    try:
        if current_user["role"] not in [
            "super_admin",
            "sub_admin"
        ]:
            raise HTTPException(
                status_code=403,
                detail="Only admins can view activity logs"
            )

        return await activity_service.get_activity_log(
            log_id
        )

    except Exception as e:
        raise exception_to_http(e)