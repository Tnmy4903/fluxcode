"""
Deliverables Management API
"""
from fastapi import APIRouter, Depends, HTTPException

from app.db.schemas import DeliverablesCreate, DeliverablesUpdate
from app.services.service_layer import DeliverablesService, ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

deliverables_router = APIRouter()
deliverables_service = DeliverablesService()
activity_service = ActivityLogService()


@deliverables_router.post("/projects/{project_id}/deliverables", response_model=dict)
async def create_deliverables(project_id: str, deliverables: DeliverablesCreate, current_user: dict = Depends(get_current_user)):
    """Create/Initialize deliverables for project (Admins only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can create deliverables")
        
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if deliverables already exist
        existing = await deliverables_service.deliverables_repo.find_by_project(project_id)
        if existing:
            raise HTTPException(status_code=400, detail="Deliverables already exist for this project")
        
        del_dict = deliverables.dict()
        result = await deliverables_service.create_deliverables(project_id=project_id, **del_dict)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Deliverables Created", "Project", project_id
        )
        
        logger_project.info(f"Deliverables created for project {project_id}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@deliverables_router.get("/projects/{project_id}/deliverables", response_model=dict)
async def get_deliverables(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get project deliverables"""
    try:
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check access
        if current_user["role"] == "client" and str(project["userId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        deliverables = await deliverables_service.deliverables_repo.find_by_project(project_id)
        if not deliverables:
            raise HTTPException(status_code=404, detail="Deliverables not found for this project")
        
        deliverables["id"] = str(deliverables["_id"])
        return deliverables
    except Exception as e:
        raise exception_to_http(e)


@deliverables_router.put("/projects/{project_id}/deliverables", response_model=dict)
async def update_deliverables(project_id: str, updates: DeliverablesUpdate, current_user: dict = Depends(get_current_user)):
    """Update project deliverables (Admins only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can update deliverables")
        
        from app.repositories import ProjectRepository
        project_repo = ProjectRepository()
        project = await project_repo.find_by_id(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        update_dict = updates.dict(exclude_unset=True)
        result = await deliverables_service.update_deliverables(project_id, **update_dict)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Deliverables Updated", "Project", project_id
        )
        
        logger_project.info(f"Deliverables updated for project {project_id}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@deliverables_router.delete("/projects/{project_id}/deliverables", response_model=dict)
async def delete_deliverables(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete project deliverables (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can delete deliverables")
        
        deliverables = await deliverables_service.deliverables_repo.find_by_project(project_id)
        if not deliverables:
            raise HTTPException(status_code=404, detail="Deliverables not found")
        
        deleted = await deliverables_service.deliverables_repo.delete(str(deliverables["_id"]))
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Deliverables Deleted", "Project", project_id
        )
        
        return {"message": "Deliverables deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)
