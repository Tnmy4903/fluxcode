from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from bson import ObjectId
import os

from app.api.auth import get_current_user
from app.db.database import db
from app.db.schemas import FileUploadOut

upload_router = APIRouter()

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ───────────────────────────────
# ⬆️ Upload File (Client Only)
# ───────────────────────────────
@upload_router.post("/", response_model=FileUploadOut)
async def upload_file(
    file: UploadFile = File(...),
    projectId: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can upload files")

    project = await db.projects.find_one({
        "_id": ObjectId(projectId),
        "userId": ObjectId(current_user["id"])
    })
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    ext = file.filename.split(".")[-1]
    saved_name = f"{uuid4().hex}.{ext}"
    saved_path = UPLOAD_DIR / saved_name

    with open(saved_path, "wb") as buffer:
        buffer.write(await file.read())

    upload_doc = {
        "userId": ObjectId(current_user["id"]),
        "projectId": ObjectId(projectId),
        "fileName": file.filename,
        "filePath": str(saved_path),
        "uploadedAt": datetime.utcnow()
    }

    result = await db.uploads.insert_one(upload_doc)
    upload_doc["id"] = str(result.inserted_id)
    upload_doc["userId"] = str(upload_doc["userId"])
    upload_doc["projectId"] = str(upload_doc["projectId"])

    return FileUploadOut(**upload_doc)


# ───────────────────────────────
# 📄 Download Uploaded File (Admin Only)
# ───────────────────────────────
@upload_router.get("/{filename}")
async def get_uploaded_file(filename: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only access")

    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file_path, filename=filename)

