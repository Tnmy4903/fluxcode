"""
Quotation Management API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from app.db.schemas import QuotationCreate, QuotationUpdate, QuotationOut
from app.services.service_layer import QuotationService, ActivityLogService, NotificationService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

quotation_router = APIRouter()
quotation_service = QuotationService()
activity_service = ActivityLogService()
notification_service = NotificationService()


@quotation_router.post("/quotations", response_model=dict)
async def create_quotation(quotation: QuotationCreate, current_user: dict = Depends(get_current_user)):
    """Create new quotation (Super Admin or Sub Admin only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can create quotations")
        
        result = await quotation_service.create_quotation(
            client_id=quotation.clientId,
            lead_id=quotation.leadId,
            project_id=quotation.projectId,
            services=quotation.services,
            items=[item.dict() for item in quotation.items],
            timeline=quotation.timeline,
            validity=quotation.validity,
            terms=quotation.terms,
            notes=quotation.notes
        )
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Quotation Created", "Quotation", result["id"]
        )
        
        logger_project.info(f"Quotation created: {result['quotationNumber']} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.get("/quotations", response_model=List[dict])
async def get_quotations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get quotations"""
    try:
        if current_user["role"] == "client":
            # Clients can only see their own quotations
            quotations = await quotation_service.quotation_repo.find_by_client(current_user["id"], skip, limit)
        elif current_user["role"] in ["super_admin", "sub_admin"]:
            if status:
                quotations = await quotation_service.quotation_repo.find_by_status(status, skip, limit)
            else:
                quotations = await quotation_service.quotation_repo.get_all_sorted(skip, limit)
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
        for q in quotations:
            q["id"] = str(q["_id"])
        
        return quotations
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.get("/quotations/{quotation_id}", response_model=dict)
async def get_quotation(quotation_id: str, current_user: dict = Depends(get_current_user)):
    """Get quotation details"""
    try:
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        # Verify access
        if current_user["role"] == "client" and str(quotation["clientId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        quotation["id"] = str(quotation["_id"])
        return quotation
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.put("/quotations/{quotation_id}", response_model=dict)
async def update_quotation(quotation_id: str, updates: QuotationUpdate, current_user: dict = Depends(get_current_user)):
    """Update quotation (Admins only)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can update quotations")
        
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        update_dict = updates.dict(exclude_unset=True)

        if "items" in update_dict:
            update_dict["items"] = [item.dict() for item in update_dict["items"]]

        result = await quotation_service.update_quotation(
            quotation_id=quotation_id,
            revised_by=current_user["id"],
            **update_dict
        )

        return result
    except Exception as e:
        raise exception_to_http(e)

@quotation_router.post("/quotations/{quotation_id}/send", response_model=dict)
async def send_quotation(quotation_id: str, current_user: dict = Depends(get_current_user)):
    """Send quotation to client (Mark as Sent)"""
    try:
        if current_user["role"] not in ["super_admin", "sub_admin"]:
            raise HTTPException(status_code=403, detail="Only admins can send quotations")
        
        result = await quotation_service.send_quotation(quotation_id)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Quotation Sent", "Quotation", quotation_id
        )
        
        # Create notification for client
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        await notification_service.create_notification(
            str(quotation["clientId"]), "quotation_sent",
            "Quotation Sent", f"Quotation {quotation['quotationNumber']} has been sent",
            quotation_id, "Quotation"
        )
        
        logger_project.info(f"Quotation sent: {quotation['quotationNumber']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.post("/quotations/{quotation_id}/accept", response_model=dict)
async def accept_quotation(quotation_id: str, current_user: dict = Depends(get_current_user)):
    """Accept quotation (Client only)"""
    try:
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        if str(quotation["clientId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await quotation_service.accept_quotation(quotation_id, current_user["id"])
        logger_project.info(f"Quotation accepted: {quotation['quotationNumber']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.post("/quotations/{quotation_id}/reject", response_model=dict)
async def reject_quotation(quotation_id: str, current_user: dict = Depends(get_current_user)):
    """Reject quotation (Client only)"""
    try:
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        if str(quotation["clientId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await quotation_service.update_quotation_status(quotation_id, "Rejected")
        logger_project.info(f"Quotation rejected: {quotation['quotationNumber']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.post("/quotations/{quotation_id}/request-revision", response_model=dict)
async def request_revision(quotation_id: str, current_user: dict = Depends(get_current_user)):
    """Request revision on quotation (Client only)"""
    try:
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        if str(quotation["clientId"]) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = await quotation_service.update_quotation_status(quotation_id, "Revision Requested")
        logger_project.info(f"Revision requested: {quotation['quotationNumber']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@quotation_router.delete("/quotations/{quotation_id}", response_model=dict)
async def delete_quotation(quotation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete quotation (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can delete quotations")
        
        quotation = await quotation_service.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        deleted = await quotation_service.quotation_repo.delete(quotation_id)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Quotation Deleted", "Quotation", quotation_id
        )
        
        return {"message": "Quotation deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)
