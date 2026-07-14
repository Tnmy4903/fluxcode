from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel
from bson import ObjectId

from app.db.database import db
from app.db.schemas import ProjectOut, InvoiceOut
from app.api.auth import get_current_user

project_router = APIRouter()
invoice_router = APIRouter()


# ───────────────────────────────
# 📦 Client: View Own Projects
# ───────────────────────────────
@project_router.get("/", response_model=List[ProjectOut])
async def get_my_projects(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Only clients can view their projects")

    cursor = db.projects.find({"userId": ObjectId(current_user["id"])}).sort("createdAt", -1)
    projects = []
    async for proj in cursor:
        proj["id"] = str(proj["_id"])
        proj["userId"] = str(proj["userId"])
        projects.append(ProjectOut(**proj))
    return projects


# ───────────────────────────────
# 🧾 Client: View Invoice by Project
# ───────────────────────────────
@invoice_router.get("/{project_id}", response_model=InvoiceOut)
async def get_invoice_by_project(project_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Clients only")

    invoice = await db.invoices.find_one({"projectId": ObjectId(project_id)})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    project = await db.projects.find_one({
        "_id": ObjectId(project_id),
        "userId": ObjectId(current_user["id"])
    })
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    invoice["id"] = str(invoice["_id"])
    invoice["projectId"] = str(invoice["projectId"])
    return InvoiceOut(**invoice)


# ───────────────────────────────
# 🧾 Admin: Mark Invoice as Paid/Unpaid
# ───────────────────────────────
class PaymentUpdate(BaseModel):
    isPaid: bool


@invoice_router.patch("/{invoice_id}")
async def update_invoice_payment(invoice_id: str, payload: PaymentUpdate, current_user: dict = Depends(get_current_user)):
    # Only super_admin can update invoice payment status
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can update payment status")

    result = await db.invoices.update_one(
        {"_id": ObjectId(invoice_id)},
        {"$set": {
            "isPaid": payload.isPaid,
            "updatedAt": datetime.utcnow()
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found or already set")

    return {"message": "Payment status updated", "isPaid": payload.isPaid}

