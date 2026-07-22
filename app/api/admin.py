from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user
from app.services.admin_service import AdminService
from app.core.exceptions import AuthenticationException

admin_router = APIRouter()

admin_service = AdminService()


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def require_admin(current_user: dict):
    """
    Allow only Super Admin and Sub Admin.
    """
    if current_user.get("role") not in ["super_admin", "sub_admin"]:
        raise AuthenticationException("Admin access only")


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@admin_router.get("/dashboard")
async def admin_dashboard(
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    return await admin_service.get_dashboard(current_user)


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

@admin_router.get("/summary")
async def get_summary(
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    return await admin_service.get_summary()


# ------------------------------------------------------------------
# Recent Activities
# ------------------------------------------------------------------

@admin_router.get("/recent-activities")
async def recent_activities(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of recent activities"
    ),
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    return await admin_service.get_recent_activities(limit)


# ------------------------------------------------------------------
# System Statistics
# ------------------------------------------------------------------

@admin_router.get("/system-stats")
async def system_stats(
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    return await admin_service.get_system_stats()
