from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from uuid import uuid4
from pathlib import Path
import os

from app.api.auth import get_current_user
from app.db.database import db
from app.db.schemas import (
    ProjectOut, FileUploadOut, InvoiceOut
)
from app.services.invoice_generator import generate_invoice_pdf
from app.services.email import send_invoice_email

admin_router = APIRouter()


# ───────────────────────────────
# 🧠 Admin Welcome Route
# ───────────────────────────────
@admin_router.get("/dashboard")
async def admin_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"message": f"Welcome Admin {current_user['name']}"}


# ───────────────────────────────
# 📁 Project Management
# ───────────────────────────────
@admin_router.get("/projects", response_model=List[ProjectOut])
async def get_all_projects(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only access")

    cursor = db.projects.find().sort("createdAt", -1)
    projects = []
    async for proj in cursor:
        proj["id"] = str(proj["_id"])
        proj["userId"] = str(proj["userId"])
        projects.append(ProjectOut(**proj))
    return projects


class StatusUpdate(BaseModel):
    status: str  # expected: pending, accepted, in_progress, delivered


@admin_router.patch("/projects/{id}/status")
async def update_project_status(id: str, payload: StatusUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only access")

    if payload.status not in ["pending", "accepted", "in_progress", "delivered"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = await db.projects.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": payload.status, "updatedAt": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project not found or already set")

    return {"message": "Status updated successfully", "newStatus": payload.status}


class BudgetUpdate(BaseModel):
    budget: float


@admin_router.patch("/projects/{id}/budget")
async def update_project_budget(id: str, payload: BudgetUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only access")

    result = await db.projects.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"budget": payload.budget, "updatedAt": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project not found or no update made")

    return {"message": "Budget updated successfully", "newBudget": payload.budget}


# ───────────────────────────────
# 🧾 Invoice Generation
# ───────────────────────────────
@admin_router.post("/projects/{id}/invoice", response_model=InvoiceOut)
async def generate_invoice(id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only access")

    project = await db.projects.find_one({"_id": ObjectId(id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = await db.users.find_one({"_id": project["userId"]})
    if not user:
        raise HTTPException(status_code=404, detail="Client not found")

    now = datetime.utcnow()
    invoice_data = {
        "client_name": user["name"],
        "client_email": user["email"],
        "title": project["title"],
        "description": project["description"],
        "status": project["status"],
        "amount": project["budget"] or 0.0,
        "currency": "INR",
        "invoice_number": f"INV-{uuid4().hex[:8].upper()}",
        "deadline": project["deadline"].strftime("%Y-%m-%d") if project.get("deadline") else "N/A",
        "generated_on": now.strftime("%Y-%m-%d"),
    }

    path = Path("app/uploads/invoices")
    pdf_path = generate_invoice_pdf(invoice_data, path)

    doc = {
        "projectId": project["_id"],
        "fileUrl": str(pdf_path),
        "amount": invoice_data["amount"],
        "invoiceNumber": invoice_data["invoice_number"],
        "isPaid": False,
        "currency": invoice_data["currency"],
        "generatedOn": now
    }

    result = await db.invoices.insert_one(doc)

    doc["id"] = str(result.inserted_id)
    doc["projectId"] = str(doc["projectId"])
    return InvoiceOut(**doc)


# ───────────────────────────────
# 📂 Admin Upload Manager
# ───────────────────────────────
@admin_router.get("/uploads", response_model=List[FileUploadOut])
async def list_all_uploads(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    cursor = db.uploads.find().sort("uploadedAt", -1)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["userId"] = str(doc["userId"])
        doc["projectId"] = str(doc["projectId"])
        results.append(FileUploadOut(**doc))
    return results


@admin_router.delete("/uploads/{id}")
async def delete_upload(id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    upload = await db.uploads.find_one({"_id": ObjectId(id)})
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    file_path = upload["filePath"]
    if os.path.exists(file_path):
        os.remove(file_path)

    await db.uploads.delete_one({"_id": ObjectId(id)})
    return {"message": "Upload deleted successfully"}


# ───────────────────────────────
# 📊 Admin Summary Endpoint
# ───────────────────────────────
@admin_router.get("/summary")
async def get_admin_summary(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    total_users = await db.users.count_documents({})
    admin_count = await db.users.count_documents({"role": "admin"})
    client_count = await db.users.count_documents({"role": "client"})

    total_projects = await db.projects.count_documents({})
    pending = await db.projects.count_documents({"status": "pending"})
    in_progress = await db.projects.count_documents({"status": "in_progress"})
    delivered = await db.projects.count_documents({"status": "delivered"})

    upload_count = await db.uploads.count_documents({})
    contact_count = await db.contact_forms.count_documents({})
    subscriber_count = await db.newsletter.count_documents({})

    total_invoices = await db.invoices.count_documents({})
    paid = await db.invoices.count_documents({"isPaid": True})
    unpaid = await db.invoices.count_documents({"isPaid": False})

    return {
        "users": {
            "total": total_users,
            "admins": admin_count,
            "clients": client_count
        },
        "projects": {
            "total": total_projects,
            "pending": pending,
            "in_progress": in_progress,
            "delivered": delivered
        },
        "uploads": upload_count,
        "contacts": contact_count,
        "subscribers": subscriber_count,
        "invoices": {
            "total": total_invoices,
            "paid": paid,
            "unpaid": unpaid
        }
    }


# ───────────────────────────────
# 📧 Email Invoice to Client
# ───────────────────────────────
@admin_router.post("/invoices/{invoice_id}/send")
async def send_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    invoice = await db.invoices.find_one({"_id": ObjectId(invoice_id)})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    project = await db.projects.find_one({"_id": invoice["projectId"]})
    if not project:
        raise HTTPException(status_code=404, detail="Linked project not found")

    user = await db.users.find_one({"_id": project["userId"]})
    if not user:
        raise HTTPException(status_code=404, detail="Client not found")

    file_path = invoice["fileUrl"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Invoice file missing")

    subject = f"\ud83d\udccc Invoice #{invoice['invoiceNumber']} for '{project['title']}'"
    body = f"""Hello {user['name']},

Please find attached the invoice for your project titled: {project['title']}.

Amount: ₹{invoice['amount']}  
Status: {'PAID' if invoice['isPaid'] else 'UNPAID'}  
Date: {invoice['generatedOn'].strftime('%Y-%m-%d')}

Regards,  
Tanmay (FluxCode)
"""

    response = send_invoice_email(user["email"], subject, body, file_path)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Mailgun failed to send email")

    return {"message": "Invoice emailed successfully to client", "email": user["email"]}
