"""
Project Discussions API
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.schemas import DiscussionMessageCreate, DiscussionReplyCreate
from app.services.service_layer import DiscussionService, ActivityLogService, NotificationService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

discussion_router = APIRouter()
discussion_service = DiscussionService()
activity_service = ActivityLogService()
notification_service = NotificationService()


@discussion_router.post("/projects/{project_id}/discussions", response_model=dict)
async def add_message(project_id: str, msg: DiscussionMessageCreate, current_user: dict = Depends(get_current_user)):
    """Add message to project discussion"""
    try:
        # Verify user has access to project
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check access
        if current_user["role"] == "client" and str(project["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await discussion_service.add_message(
            project_id=project_id,
            author_id=current_user["id"],
            author_name=current_user["name"],
            message=msg.message,
            attachments=msg.attachments
        )
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Discussion Message Added", "Project", project_id
        )
        
        logger_project.info(f"Discussion message added to project {project_id}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@discussion_router.get("/projects/{project_id}/discussions", response_model=list)
async def get_project_discussions(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get all messages in project discussion"""
    try:
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check access
        if current_user["role"] == "client" and str(project["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        messages = await discussion_service.get_project_discussion(project_id, skip, limit)
        return messages
    except Exception as e:
        raise exception_to_http(e)


@discussion_router.post("/discussions/{message_id}/replies", response_model=dict)
async def add_reply(message_id: str, reply: DiscussionReplyCreate, current_user: dict = Depends(get_current_user)):
    """Add reply to discussion message"""
    try:
        message = await discussion_service.discussion_repo.find_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify access to project
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(str(message["projectId"]))
        
        if current_user["role"] == "client" and str(project["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await discussion_service.add_reply(
            message_id=message_id,
            author_id=current_user["id"],
            author_name=current_user["name"],
            message=reply.message,
            attachments=reply.attachments
        )
        
        return result
    except Exception as e:
        raise exception_to_http(e)


@discussion_router.get("/discussions/{message_id}", response_model=dict)
async def get_message(message_id: str, current_user: dict = Depends(get_current_user)):
    """Get message and all its replies"""
    try:
        message = await discussion_service.discussion_repo.find_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(str(message["projectId"]))
        
        if current_user["role"] == "client" and str(project["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        message["id"] = str(message["_id"])
        
        # Mark as seen
        await discussion_service.discussion_repo.mark_seen(message_id)
        message["seen"] = True
        
        return message
    except Exception as e:
        raise exception_to_http(e)


@discussion_router.delete("/discussions/{message_id}", response_model=dict)
async def delete_message(message_id: str, current_user: dict = Depends(get_current_user)):
    """Delete discussion message (Author or Super Admin only)"""
    try:
        message = await discussion_service.discussion_repo.find_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check permission
        if current_user["role"] != "super_admin" and str(message["authorId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        deleted = await discussion_service.discussion_repo.delete(message_id)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Discussion Message Deleted", "Discussion Message", message_id
        )
        
        return {"message": "Message deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)
