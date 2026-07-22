from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.auth import get_current_user
from app.core.exceptions import AuthenticationException
from app.db.schemas import FileUploadOut
from app.services.service_layer import UploadService


upload_router = APIRouter()

upload_service = UploadService()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def require_client(current_user: dict):
    if current_user.get("role") != "client":
        raise AuthenticationException(
            "Only clients can access this endpoint."
        )


def require_admin(current_user: dict):
    if current_user.get("role") not in (
        "super_admin",
        "sub_admin",
    ):
        raise AuthenticationException(
            "Admin access only."
        )


def require_super_admin(current_user: dict):
    if current_user.get("role") != "super_admin":
        raise AuthenticationException(
            "Only Super Admin can perform this action."
        )


# ------------------------------------------------------------------
# Client - Upload File
# ------------------------------------------------------------------

@upload_router.post(
    "/",
    response_model=FileUploadOut,
)
async def upload_file(
    file: UploadFile = File(...),
    projectId: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    require_client(current_user)

    return await upload_service.upload_file(
        file=file,
        project_id=projectId,
        current_user=current_user,
    )


# ------------------------------------------------------------------
# Admin - Get All Uploads
# ------------------------------------------------------------------

@upload_router.get(
    "/list",
    response_model=List[FileUploadOut],
)
async def get_all_uploads(
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)

    return await upload_service.get_all_uploads()


# ------------------------------------------------------------------
# Admin - Download File
# ------------------------------------------------------------------

@upload_router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    require_super_admin(current_user)

    file_path = await upload_service.download_file(
        filename
    )

    return FileResponse(
        path=str(file_path),
        filename=filename,
    )


# ------------------------------------------------------------------
# Admin - Delete Upload
# ------------------------------------------------------------------

@upload_router.delete("/{upload_id}")
async def delete_upload(
    upload_id: str,
    current_user: dict = Depends(get_current_user),
):
    require_super_admin(current_user)

    await upload_service.delete_upload(
        upload_id
    )

    return {
        "message": "Upload deleted successfully."
    }