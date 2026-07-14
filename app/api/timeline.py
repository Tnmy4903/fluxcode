"""
Project Timeline API
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.schemas import TimelineEventCreate, TimelineEventOut
from app.services.service_layer import TimelineService, ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

timeline_router = APIRouter()
timeline_service = TimelineService()
activity_service = ActivityLogService()


@timeline_router.post("/projects/{project_id}/timeline", response_model=dict)
async def add_timeline_event(project_id: str, event: TimelineEventCreate, current_user: dict = Depends(get_current_user)):
    """Add timeline event to project (Admins only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can add timeline events")
        
        result = await timeline_service.add_timeline_event(
            project_id=project_id,
            title=event.title,
            description=event.description,
            created_by=current_user["id"]
        )
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Timeline Event Added", "Project", project_id,
            {"event": event.title}
        )
        
        logger_project.info(f"Timeline event added: {result['id']} to project {project_id}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@timeline_router.get("/projects/{project_id}/timeline", response_model=list)
async def get_project_timeline(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get project timeline"""
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
        
        events = await timeline_service.get_project_timeline(project_id, skip, limit)
        return events
    except Exception as e:
        raise exception_to_http(e)


@timeline_router.delete("/timeline/{event_id}", response_model=dict)
async def delete_timeline_event(event_id: str, current_user: dict = Depends(get_current_user)):
    """Delete timeline event (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can delete timeline events")
        
        event = await timeline_service.timeline_repo.find_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Timeline event not found")
        
        deleted = await timeline_service.timeline_repo.delete(event_id)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Timeline Event Deleted", "Timeline Event", event_id
        )
        
        return {"message": "Timeline event deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)
