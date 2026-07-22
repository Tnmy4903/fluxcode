"""
Quotation Management API
"""

from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user
from app.core.exceptions import AuthenticationException
from app.db.schemas import (
    QuotationCreate,
    QuotationUpdate,
    QuotationOut,
)
from app.exceptions import exception_to_http
from app.services.service_layer import QuotationService


quotation_router = APIRouter()

quotation_service = QuotationService()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

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
# Create Quotation
# ------------------------------------------------------------------

@quotation_router.post(
    "/quotations",
    response_model=QuotationOut,
)
async def create_quotation(
    quotation: QuotationCreate,
    current_user: dict = Depends(get_current_user),
):
    try:

        require_admin(current_user)

        return await quotation_service.create_quotation(
            client_id=quotation.clientId,
            lead_id=quotation.leadId,
            project_id=quotation.projectId,
            services=quotation.services,
            items=[item.dict() for item in quotation.items],
            timeline=quotation.timeline,
            validity=quotation.validity,
            terms=quotation.terms,
            notes=quotation.notes,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Get Quotations
# ------------------------------------------------------------------

@quotation_router.get(
    "/quotations",
    response_model=List[QuotationOut],
)
async def get_quotations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query(None),
    current_user: dict = Depends(get_current_user),
):
    try:

        return await quotation_service.get_quotations(
            current_user=current_user,
            skip=skip,
            limit=limit,
            status=status,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Get Quotation
# ------------------------------------------------------------------

@quotation_router.get(
    "/quotations/{quotation_id}",
    response_model=QuotationOut,
)
async def get_quotation(
    quotation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:

        return await quotation_service.get_quotation(
            quotation_id,
            current_user,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Update Quotation
# ------------------------------------------------------------------

@quotation_router.put(
    "/quotations/{quotation_id}",
    response_model=QuotationOut,
)
async def update_quotation(
    quotation_id: str,
    updates: QuotationUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:

        require_admin(current_user)

        update_dict = updates.dict(
            exclude_unset=True
        )

        if "items" in update_dict:
            update_dict["items"] = [
                item.dict()
                for item in update_dict["items"]
            ]

        return await quotation_service.update_quotation(
            quotation_id=quotation_id,
            revised_by=current_user["id"],
            **update_dict,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Send Quotation
# ------------------------------------------------------------------

@quotation_router.post(
    "/quotations/{quotation_id}/send",
    response_model=QuotationOut,
)
async def send_quotation(
    quotation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:

        require_admin(current_user)

        return await quotation_service.send_quotation(
            quotation_id,
            current_user,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Accept Quotation
# ------------------------------------------------------------------

@quotation_router.post(
    "/quotations/{quotation_id}/accept",
    response_model=dict,
)
async def accept_quotation(
    quotation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:

        return await quotation_service.accept_quotation(
            quotation_id,
            current_user["id"],
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Reject Quotation
# ------------------------------------------------------------------

@quotation_router.post(
    "/quotations/{quotation_id}/reject",
    response_model=QuotationOut,
)
async def reject_quotation(
    quotation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:

        return await quotation_service.reject_quotation(
            quotation_id,
            current_user,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Request Revision
# ------------------------------------------------------------------

@quotation_router.post(
    "/quotations/{quotation_id}/request-revision",
    response_model=QuotationOut,
)
async def request_revision(
    quotation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:

        return await quotation_service.request_revision(
            quotation_id,
            current_user,
        )

    except Exception as e:
        raise exception_to_http(e)


# ------------------------------------------------------------------
# Delete Quotation
# ------------------------------------------------------------------

@quotation_router.delete(
    "/quotations/{quotation_id}",
    response_model=dict,
)
async def delete_quotation(
    quotation_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:

        require_super_admin(current_user)

        return await quotation_service.delete_quotation(
            quotation_id,
            current_user,
        )

    except Exception as e:
        raise exception_to_http(e)