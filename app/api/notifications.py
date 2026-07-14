"""
Notifications API
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.service_layer import NotificationService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

notification_router = APIRouter()
notification_service = NotificationService()


@notification_router.get("/notifications", response_model=list)
async def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    try:
        notifications = await notification_service.get_user_notifications(current_user["id"], skip, limit)
        return notifications
    except Exception as e:
        raise exception_to_http(e)


@notification_router.get("/notifications/unread", response_model=list)
async def get_unread_notifications(current_user: dict = Depends(get_current_user)):
    """Get unread notifications for current user"""
    try:
        notifications = await notification_service.notification_repo.find_unread_by_user(current_user["id"])
        
        for notif in notifications:
            notif["id"] = str(notif["_id"])
        
        return notifications
    except Exception as e:
        raise exception_to_http(e)


@notification_router.post("/notifications/{notification_id}/read", response_model=dict)
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    try:
        notification = await notification_service.notification_repo.find_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Verify ownership
        if str(notification["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        await notification_service.mark_as_read(notification_id)
        
        notification["id"] = str(notification["_id"])
        notification["read"] = True
        
        return notification
    except Exception as e:
        raise exception_to_http(e)


@notification_router.post("/notifications/read-all", response_model=dict)
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    try:
        count = await notification_service.mark_all_as_read(current_user["id"])
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise exception_to_http(e)


@notification_router.delete("/notifications/{notification_id}", response_model=dict)
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete notification"""
    try:
        notification = await notification_service.notification_repo.find_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Verify ownership
        if str(notification["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        deleted = await notification_service.notification_repo.delete(notification_id)
        
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)


@notification_router.post("/notifications/clear-all", response_model=dict)
async def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Delete all notifications for current user"""
    try:
        notifications = await notification_service.notification_repo.find_by_user(current_user["id"], 0, 10000)
        
        count = 0
        for notif in notifications:
            if await notification_service.notification_repo.delete(str(notif["_id"])):
                count += 1
        
        return {"message": f"Deleted {count} notifications"}
    except Exception as e:
        raise exception_to_http(e)
