from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.services.invoice_service import InvoiceService
from app.core.exceptions import AuthenticationException
from app.db.schemas import InvoiceOut, PaymentUpdate


invoice_router = APIRouter()

invoice_service = InvoiceService()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def require_client(current_user: dict):
    if current_user.get("role") != "client":
        raise AuthenticationException(
            "Only clients can access this endpoint."
        )


def require_admin(current_user: dict):
    if current_user.get("role") not in [
        "super_admin",
        "sub_admin"
    ]:
        raise AuthenticationException(
            "Admin access only."
        )


def require_super_admin(current_user: dict):
    if current_user.get("role") != "super_admin":
        raise AuthenticationException(
            "Only Super Admin can perform this action."
        )


# ------------------------------------------------------------------
# Client - View Invoice by Project
# ------------------------------------------------------------------

@invoice_router.get(
    "/project/{project_id}",
    response_model=InvoiceOut
)
async def get_invoice_by_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    require_client(current_user)

    return await invoice_service.get_invoice_by_project(
        project_id=project_id,
        current_user_id=current_user["id"]
    )


# ------------------------------------------------------------------
# Admin - Get Invoice by Invoice ID
# ------------------------------------------------------------------

@invoice_router.get(
    "/{invoice_id}",
    response_model=InvoiceOut
)
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    require_admin(current_user)

    return await invoice_service.get_invoice(
        invoice_id
    )


# ------------------------------------------------------------------
# Admin - Send Invoice
# ------------------------------------------------------------------

@invoice_router.post(
    "/{invoice_id}/send"
)
async def send_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    require_super_admin(current_user)

    return await invoice_service.send_invoice_to_client(
        invoice_id
    )


# ------------------------------------------------------------------
# Admin - Update Payment Status
# ------------------------------------------------------------------

@invoice_router.patch(
    "/{invoice_id}/payment"
)
async def update_payment_status(
    invoice_id: str,
    payload: PaymentUpdate,
    current_user: dict = Depends(get_current_user)
):
    require_super_admin(current_user)

    await invoice_service.update_payment_status(
        invoice_id=invoice_id,
        is_paid=payload.isPaid
    )

    return {
        "message": "Invoice payment status updated successfully."
    }