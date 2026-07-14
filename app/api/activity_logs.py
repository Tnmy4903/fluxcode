"""
Activity Logs API
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.service_layer import ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

activity_router = APIRouter()
activity_service = ActivityLogService()


@activity_router.get("/activity-logs", response_model=list)
async def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs (Admins only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can view activity logs")
        
        logs = await activity_service.activity_repo.get_all_sorted(skip, limit)
        
        for log in logs:
            log["id"] = str(log["_id"])
        
        return logs
    except Exception as e:
        raise exception_to_http(e)


@activity_router.get("/activity-logs/user/{user_id}", response_model=list)
async def get_user_activity_logs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get activity logs for specific user (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can view user activity")
        
        logs = await activity_service.activity_repo.find_by_user(user_id, skip, limit)
        
        for log in logs:
            log["id"] = str(log["_id"])
        
        return logs
    except Exception as e:
        raise exception_to_http(e)


@activity_router.get("/activity-logs/entity/{entity_id}", response_model=list)
async def get_entity_activity(
    entity_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get activity history for entity"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can view activity logs")
        
        logs = await activity_service.get_entity_history(entity_id, skip, limit)
        return logs
    except Exception as e:
        raise exception_to_http(e)


@activity_router.get("/activity-logs/{log_id}", response_model=dict)
async def get_activity_log(log_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific activity log"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can view activity logs")
        
        log = await activity_service.activity_repo.find_by_id(log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Activity log not found")
        
        log["id"] = str(log["_id"])
        return log
    except Exception as e:
        raise exception_to_http(e)
