"""
Service layer for business logic
"""
from datetime import datetime
from uuid import uuid4
from backend.app.db.schemas import QuotationStatus, RequirementStatus
from bson import ObjectId
from pathlib import Path
import secrets
import os
from fastapi import UploadFile

from app.repositories import (
    UserRepository, ProjectRepository, InvoiceRepository, UploadRepository, BlogRepository, ContactRepository,
    LeadRepository, RequirementRepository, QuotationRepository, TimelineRepository, DiscussionRepository, DeliverablesRepository, ActivityLogRepository,
    NotificationRepository, PortfolioRepository, WebsiteContentRepository
)
from app.db.models import hash_password, verify_password
from app.exceptions import (
    AuthenticationException, ResourceNotFoundException, DuplicateException, PermissionException, ValidationException
)
from app.logger import logger_auth, logger_admin, logger_project, logger_blog, logger_contact, logger_lead, logger_requirement, logger_quotation, logger_timeline, logger_discussion, logger_deliverables, logger_activity, logger_notification, logger_portfolio, logger_website, logger_invoice, logger_upload
from app.services.email import send_contact_alert, send_invoice_email
from app.services.invoice_generator import generate_invoice_pdf

class AuthService:
    """Authentication business logic"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def register_client(self, name: str, email: str, phone: str, password: str) -> dict:
        """Register new client user"""

        email = email.strip().lower()
        name = name.strip()
        phone = phone.strip()

        if await self.user_repo.email_exists(email):
            logger_auth.warning(f"Registration failed: email {email} already exists")
            raise DuplicateException("Email")
        
        user_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "passwordHash": hash_password(password),
            "role": "client"
        }
        
        user_id = await self.user_repo.create(user_data)
        logger_auth.info(f"New client registered: {email}")
        
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": "client"
        }
    
    async def verify_credentials(self, email: str, password: str) -> dict:
        """Verify user credentials"""
        email = email.strip().lower()
        user = await self.user_repo.find_by_email(email)
        
        if not user or not verify_password(password, user["passwordHash"]):
            logger_auth.warning(f"Login failed for user: {email[:3]}***")
            raise AuthenticationException("Invalid email or password")
        
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    
    async def create_sub_admin(self, email: str, name: str) -> dict:
        """Create new sub-admin (Super Admin only)"""
        email = email.strip().lower()
        name = name.strip()

        if await self.user_repo.email_exists(email):
            raise DuplicateException("Email")
        
        temp_password = secrets.token_urlsafe(12)
        user_data = {
            "name": name,
            "email": email,
            "phone": None,
            "passwordHash": hash_password(temp_password),
            "role": "sub_admin"
        }
        
        user_id = await self.user_repo.create(user_data)
        logger_auth.info(f"New sub-admin created: {email}")
        
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": None,
            "role": "sub_admin"
        }
    
    async def promote_to_sub_admin(self, user_id: str) -> dict:
        """Promote client to sub-admin"""
        user = await self.user_repo.find_by_id(user_id)
        
        if not user:
            raise ResourceNotFoundException("User")
        
        if user["role"] != "client":
            raise ValidationException("only clients can be promoted")
        
        updated = await self.user_repo.update(user_id, {"role": "sub_admin"})
        if not updated:
            raise ValidationException(
                "Failed to promote user."
            )
        logger_auth.info(f"Client promoted to sub-admin: {user['email']}")
        
        user["role"] = "sub_admin"
        user["id"] = str(user["_id"])
        return user
    
    async def get_current_user_profile(
        self,
        user_id: str
    ) -> dict:
        """Get current logged-in user profile"""

        user = await self.user_repo.find_by_id(user_id)

        if not user:
            raise ResourceNotFoundException("User")

        user["id"] = str(user["_id"])

        return user

class AdminService:

    def __init__(self):
        self.user_repo = UserRepository()
        self.project_repo = ProjectRepository()
        self.invoice_repo = InvoiceRepository()
        self.contact_repo = ContactRepository()
        self.activity_repo = ActivityLogRepository()

    async def get_dashboard(self, current_user: dict) -> dict:
        logger_admin.info(
            f"Dashboard accessed by {current_user.get('email')}"
        )

        role = current_user.get("role")

        if role not in ["super_admin", "sub_admin"]:
            raise ValidationException("Admin access only")

        role_display = (
            "Super Admin"
            if role == "super_admin"
            else "Sub Admin"
        )

        return {
            "message": f"Welcome {role_display} {current_user.get('name')}",
            "role": role
        }
    
    async def get_summary(self) -> dict:

        total_users = await self.user_repo.count({})
        admin_count = await self.user_repo.get_admin_count()
        client_count = await self.user_repo.count_by_role("client")
        total_projects = await self.project_repo.count_all()
        pending = await self.project_repo.count_by_status("pending")
        accepted = await self.project_repo.count_by_status("accepted")
        in_progress = await self.project_repo.count_by_status("in_progress")
        testing = await self.project_repo.count_by_status("testing")
        deployment = await self.project_repo.count_by_status("deployment")
        delivered = await self.project_repo.count_by_status("delivered")
        completed = await self.project_repo.count_by_status("completed")
        total_invoices = await self.invoice_repo.count_all()
        paid = await self.invoice_repo.count_paid()
        unpaid = await self.invoice_repo.count_unpaid()
        contacts = await self.contact_repo.count_all()
        

        logger_admin.info("Admin summary generated")

        return {
            "users": {
                "total": total_users,
                "admins": admin_count,
                "clients": client_count
            },
            "projects": {
                "total": total_projects,
                "pending": pending,
                "accepted": accepted,
                "in_progress": in_progress,
                "testing": testing,
                "deployment": deployment,
                "delivered": delivered,
                "completed": completed
            },
            "contacts": contacts,
            "invoices": {
                "total": total_invoices,
                "paid": paid,
                "unpaid": unpaid
            }
        }

    async def get_recent_activities(
        self,
        limit: int = 10
    ) -> list:

        logs = await self.activity_repo.get_recent(limit)

        logger_admin.info(
            f"Fetched {len(logs)} recent activities"
        )

        return logs
    
    async def get_system_stats(self):

        recent_projects = await self.project_repo.get_recent_projects(5)
        recent_contacts = await self.contact_repo.get_recent_contacts(5)
        recent_subscribers = (
            await self.newsletter_repo.get_recent_subscribers(5)
        )

        recent_invoices = (
            await self.invoice_repo.get_recent_invoices(5)
        )

        return {
            "recent_projects": recent_projects,
            "recent_contacts": recent_contacts,
            "recent_subscribers": recent_subscribers,
            "recent_invoices": recent_invoices
        }

class ProjectService:
    """Project business logic"""
    
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.user_repo = UserRepository()
    
    async def create_project_internal(self,client_id: str,quotation_id: str,lead_id: str,title: str,description: str,deadline,budget: float,assigned_admin: str = None,assigned_sub_admin: str = None) -> dict:
        """Create new project"""
        project_data = {
            "userId": client_id,
            "quotationId": quotation_id,
            "leadId": lead_id,
            "title": title,
            "description": description,
            "deadline": deadline,
            "budget": budget,
            "assignedAdmin": assigned_admin,
            "assignedSubAdmin": assigned_sub_admin,
            "status": "pending"
        }
        
        project_id = await self.project_repo.create(project_data)
        logger_project.info(f"Project created: {project_id} by user {client_id} of quotation {quotation_id} and lead {lead_id}")
        
        return {
            "id": project_id,
            "userId": client_id,
            "quotationId": quotation_id,
            "leadId": lead_id,
            "assignedAdmin": assigned_admin,
            "assignedSubAdmin": assigned_sub_admin,
            "status": "pending",
            "title": title,
            "description": description,
            "deadline": deadline,
            "budget": budget,
        }
    
    async def create_project_from_quotation(
        self,
        quotation: dict
    ) -> dict:
        """
        Auto create project after quotation acceptance
        """
        
        if not quotation.get("clientId"):
            raise ValidationException(
                "Quotation does not contain a valid client."
            )
        
        if not quotation.get("totalAmount"):
            raise ValidationException(
                "Quotation total amount is missing."
            )

        # Prevent duplicate project
        existing = await self.project_repo.find_one({
            "quotationId": quotation["id"]
        })

        if existing:
            existing["id"] = str(existing["_id"])
            return existing

        project_data = {
            "quotationId": quotation["id"],
            "leadId": quotation.get("leadId"),
            "userId": quotation["clientId"],
            "title": quotation["services"][0] if quotation.get("services") else "New Project",
            "description": quotation.get("notes"),
            "budget": quotation["totalAmount"],
            "status": "pending"
        }

        project_id = await self.project_repo.create(project_data)

        project_data["id"] = project_id

        return project_data
    
    async def update_status(self, project_id: str, status: str) -> bool:
        """Update project status"""
        valid_transitions = {
            "pending": ["in_progress"],
            "in_progress": ["testing"],
            "testing": ["deployment"],
            "deployment": ["delivered"],
            "delivered": ["completed"],
            "completed": []
        }

        current = await self.project_repo.find_by_id(project_id)

        if not current:
            raise ResourceNotFoundException("Project")

        current_status = current.get("status", "pending")

        if current_status not in valid_transitions:
            raise ValidationException(
                f"Invalid current project status: {current_status}"
            )
        
        if current_status == status:
            raise ValidationException(
                f"Project is already in '{status}' status."
            )

        if status not in valid_transitions:
            raise ValidationException("Invalid project status")

        if status not in valid_transitions[current_status]:
            raise ValidationException(
                f"Cannot change project status from "
                f"{current_status} to {status}"
            )    
        
        updated = await self.project_repo.update(project_id, {"status": status})

        if not updated:
            raise ValidationException(
                "Failed to update project status."
            )
        
        if updated:
            logger_project.info(f"Project {project_id} status updated to {status}")
        
        return updated
    
    async def set_budget(self, project_id: str, budget: float) -> bool:
        """Set project budget/price"""

        if budget <= 0:
            raise ValidationException(
                "Budget must be greater than zero."
            )
        
        updated = await self.project_repo.update(project_id, {"budget": budget})

        if not updated:
            raise ValidationException(
                "Failed to update project budget."
            )
        
        if updated:
            logger_project.info(f"Project {project_id} budget set to {budget}")
        
        return updated

    async def get_my_projects(
        self,
        user_id: str
    ) -> list:

        projects = await self.project_repo.find_by_user(user_id)

        for project in projects:
            project["id"] = str(project["_id"])

        logger_project.info(
            f"Fetched {len(projects)} projects for user {user_id}"
        )

        return projects
    
    async def get_all_projects(self) -> list:

        projects = await self.project_repo.get_all_sorted()

        for project in projects:
            project["id"] = str(project["_id"])

        logger_project.info(
            f"Fetched {len(projects)} projects"
        )

        return projects
    
    async def get_project_by_id(
        self,
        project_id: str
    ):

        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException(
                "Project"
            )

        return project
    
    async def assign_admin(
        self,
        project_id: str,
        admin_id: str
    ):

        updated = await self.project_repo.update(
            project_id,
            {
                "assignedAdmin": admin_id
            }
        )

        if not updated:
            raise ValidationException(
                "Unable to assign admin."
            )

        logger_project.info(
            f"Admin {admin_id} assigned to project {project_id}"
        )

        return updated
    
    async def assign_sub_admin(
        self,
        project_id: str,
        sub_admin_id: str
    ):

        updated = await self.project_repo.update(
            project_id,
            {
                "assignedSubAdmin": sub_admin_id
            }
        )

        if not updated:
            raise ValidationException(
                "Unable to assign sub admin."
            )

        logger_project.info(
            f"Sub Admin {sub_admin_id} assigned to {project_id}"
        )

        return updated
    
    async def delete_project(
        self,
        project_id: str
    ):

        deleted = await self.project_repo.delete(
            project_id
        )

        if not deleted:
            raise ResourceNotFoundException(
                "Project"
            )

        logger_project.info(
            f"Project deleted {project_id}"
        )

        return True
    
class InvoiceService:
    """Invoice business logic"""
    
    def __init__(self):
        self.invoice_repo = InvoiceRepository()
        self.project_repo = ProjectRepository()
        self.user_repo = UserRepository()
        self.deliverables_repo = DeliverablesRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()
        self.project_service = ProjectService()
    
    async def generate_invoice(self, project_id: str) -> dict:
        """Generate invoice PDF"""

        # Validate project
        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException("Project")

        if project["status"] != "delivered":
            raise ValidationException(
                "Invoice can only be generated after project is delivered."
            )

        if (project.get("budget") or 0) <= 0:
            raise ValidationException(
                "Project budget must be greater than zero."
            )

        # Validate deliverables
        deliverables = await self.deliverables_repo.find_by_project(project_id)

        if not deliverables:
            raise ValidationException(
                "Deliverables must be created before generating invoice."
            )

        # Prevent duplicate invoice
        existing_invoice = await self.invoice_repo.find_by_project(project_id)

        if existing_invoice:
            raise ValidationException(
                "Invoice already exists for this project."
            )

        # Validate client
        user = await self.user_repo.find_by_id(str(project["userId"]))

        if not user:
            raise ResourceNotFoundException("User")

        now = datetime.utcnow()

        invoice_data = {
            "client_name": user["name"],
            "client_email": user["email"],
            "title": project["title"],
            "description": project["description"],
            "status": project["status"],
            "amount": project.get("budget") or 0.0,
            "currency": "INR",
            "invoice_number": await self.invoice_repo.get_next_invoice_number(),
            "deadline": (
                project.get("deadline").strftime("%Y-%m-%d")
                if project.get("deadline")
                else "N/A"
            ),
            "generated_on": now.strftime("%Y-%m-%d"),
        }

        # Create invoice directory
        path = Path("app/uploads/invoices")
        path.mkdir(parents=True, exist_ok=True)

        # Generate PDF
        pdf_path = generate_invoice_pdf(invoice_data, path)

        invoice_db_data = {
            "projectId": project["_id"],
            "clientId": project["userId"],

            "invoiceNumber": invoice_data["invoice_number"],

            "title": project["title"],
            "description": project.get("description"),

            "amount": invoice_data["amount"],
            "currency": invoice_data["currency"],

            "status": "generated",
            "isPaid": False,

            "fileUrl": str(pdf_path),

            "generatedOn": now,
            "dueDate": project.get("deadline"),
            "paidOn": None,
        }

        invoice_id = await self.invoice_repo.create(invoice_db_data)

        # Activity Log
        await self.activity_service.log_activity(
            user_id="system",
            user_role="system",
            action="Invoice Generated",
            entity="Invoice",
            entity_id=invoice_id,
            details={
                "projectId": project_id,
                "invoiceNumber": invoice_data["invoice_number"]
            }
        )

        # Notify Super Admin(s)
        admins = await self.user_repo.get_by_role("super_admin")

        for admin in admins:
            await self.notification_service.create_notification(
                user_id=str(admin["_id"]),
                notif_type="invoice",
                title="Invoice Generated",
                message=f"Invoice generated for project '{project['title']}'.",
                entity_id=invoice_id,
                entity_type="Invoice"
            )

        logger_invoice.info(
            f"Invoice {invoice_id} generated for project {project_id}"
        )

        invoice_db_data["id"] = invoice_id
        invoice_db_data["projectId"] = project_id
        invoice_db_data["clientId"] = str(project["userId"])

        return invoice_db_data
    
    async def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice by ID"""

        invoice = await self.invoice_repo.find_by_id(invoice_id)

        if not invoice:
            raise ResourceNotFoundException("Invoice")

        logger_invoice.info(
            f"Fetched invoice {invoice_id}"
        )

        invoice["id"] = str(invoice["_id"])
        invoice["projectId"] = str(invoice["projectId"])
        invoice["clientId"] = str(invoice["clientId"])

        return invoice
    
    async def get_invoice_by_project(
        self,
        project_id: str,
        current_user_id: str | None = None
    ) -> dict:
        """Get invoice by project"""

        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException("Project")

        if current_user_id and str(project["userId"]) != current_user_id:
            raise PermissionException(
                "You are not authorized to access this invoice."
            )

        if not project:
            raise ResourceNotFoundException("Project")

        invoice = await self.invoice_repo.find_by_project(project_id)

        if not invoice:
            raise ResourceNotFoundException("Invoice")

        logger_invoice.info(
            f"Fetched invoice for project {project_id}"
        )

        invoice["id"] = str(invoice["_id"])
        invoice["projectId"] = str(invoice["projectId"])
        invoice["clientId"] = str(invoice["clientId"])

        return invoice

    async def send_invoice_to_client(self, invoice_id: str) -> dict:
        """Send invoice to client"""

        invoice = await self.invoice_repo.find_by_id(invoice_id)

        if not invoice:
            raise ResourceNotFoundException("Invoice")

        project = await self.project_repo.find_by_id(
            str(invoice["projectId"])
        )

        if not project:
            raise ResourceNotFoundException("Project")

        user = await self.user_repo.find_by_id(
            str(project["userId"])
        )

        if not user:
            raise ResourceNotFoundException("User")

        file_path = invoice["fileUrl"]

        if not os.path.exists(file_path):
            raise ResourceNotFoundException(
                "Invoice PDF"
            )

        subject = (
            f"📄 Invoice #{invoice['invoiceNumber']} "
            f"for '{project['title']}'"
        )

        body = f"""Hello {user['name']},

    Please find attached the invoice for your project titled: {project['title']}.

    Amount: ₹{invoice['amount']}
    Status: {'PAID' if invoice['isPaid'] else 'UNPAID'}
    Date: {invoice['generatedOn'].strftime('%Y-%m-%d')}

    Regards,
    Tanmay (FluxCode)
    """

        response = send_invoice_email(
            user["email"],
            subject,
            body,
            file_path
        )

        if response.status_code != 200:
            raise PermissionException(
                "Failed to send invoice email via Mailgun."
            )
        
        await self.invoice_repo.update(
            invoice_id,
            {
                "status": "sent"
            }
        )

        # Activity Log
        await self.activity_service.log_activity(
            user_id="system",
            user_role="system",
            action="Invoice Sent",
            entity="Invoice",
            entity_id=invoice_id,
            details={
                "email": user["email"],
                "projectId": str(project["_id"])
            }
        )

        # Notify Client
        await self.notification_service.create_notification(
            user_id=str(user["_id"]),
            notif_type="invoice",
            title="Invoice Sent",
            message="Your invoice has been emailed successfully.",
            entity_id=invoice_id,
            entity_type="Invoice"
        )

        logger_invoice.info(
            f"Invoice {invoice_id} emailed to {user['email']}"
        )

        return {
            "message": "Invoice sent successfully.",
            "email": user["email"]
        }
    
    async def update_payment_status(
        self,
        invoice_id: str,
        is_paid: bool
    ) -> bool:
        """Update invoice payment status"""

        invoice = await self.invoice_repo.find_by_id(invoice_id)

        if not invoice:
            raise ResourceNotFoundException("Invoice")

        # Prevent duplicate update
        if invoice["isPaid"] == is_paid:
            status = "paid" if is_paid else "sent"
            raise ValidationException(
                f"Invoice is already marked as {status}."
            )

        update_data = {
            "isPaid": is_paid,
            "status": "paid" if is_paid else "sent",
            "paidOn": datetime.utcnow() if is_paid else None,
        }

        updated = await self.invoice_repo.update(
            invoice_id,
            update_data
        )

        if not updated:
            raise ValidationException(
                "Failed to update invoice payment status."
            )

        status_str = "paid" if is_paid else "sent"

        logger_invoice.info(
            f"Invoice {invoice_id} marked as {status_str}"
        )

        project = await self.project_repo.find_by_id(
            str(invoice["projectId"])
        )

        if not project:
            raise ResourceNotFoundException("Project")

        # Complete project after successful payment
        if is_paid:

            if project["status"] != "delivered":
                raise ValidationException(
                    "Project must be delivered before payment can be completed."
                )

            await self.project_service.update_status(
                project_id=str(invoice["projectId"]),
                status="completed"
            )

            # Activity Log
            await self.activity_service.log_activity(
                user_id="system",
                user_role="system",
                action="Invoice Paid",
                entity="Invoice",
                entity_id=invoice_id,
                details={
                    "projectId": str(invoice["projectId"])
                }
            )

            # Notify Client
            await self.notification_service.create_notification(
                user_id=str(project["userId"]),
                notif_type="payment",
                title="Payment Received",
                message="Your payment has been successfully received.",
                entity_id=invoice_id,
                entity_type="Invoice"
            )

        return updated

class UploadService:
    """Upload business logic"""

    def __init__(self):
        self.upload_repo = UploadRepository()
        self.project_repo = ProjectRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()

    async def upload_file(
        self,
        file: UploadFile,
        project_id: str,
        current_user: dict
    ) -> dict:
        """Upload project file"""

        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException("Project")

        if str(project["userId"]) != current_user["id"]:
            raise ValidationException(
                "Project not found or access denied."
            )

        upload_dir = Path("app/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(file.filename).suffix

        saved_name = f"{uuid4().hex}{extension}"

        saved_path = upload_dir / saved_name

        content = await file.read()

        with open(saved_path, "wb") as buffer:
            buffer.write(content)

        file_size = len(content)

        upload_data = {
            "userId": ObjectId(current_user["id"]),
            "projectId": ObjectId(project_id),

            "fileName": file.filename,
            "storedFileName": saved_name,
            "filePath": str(saved_path),

            "uploadedAt": datetime.utcnow(),
            "fileSize": file_size,
            "contentType": file.content_type,
            "extension": extension,
        }

        upload_id = await self.upload_repo.create(upload_data)

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="File Uploaded",
            entity="Upload",
            entity_id=upload_id,
            details={
                "projectId": project_id,
                "fileName": file.filename
            }
        )

        await self.notification_service.create_notification(
            user_id=current_user["id"],
            notif_type="upload",
            title="File Uploaded",
            message=f"{file.filename} uploaded successfully.",
            entity_id=upload_id,
            entity_type="Upload"
        )

        logger_upload.info(
            f"Upload {upload_id} created for project {project_id}"
        )

        upload = await self.upload_repo.find_by_id(upload_id)
        upload["id"] = str(upload["_id"])
        upload["userId"] = str(upload["userId"])
        upload["projectId"] = str(upload["projectId"])

        return upload
    
    async def download_file(
        self,
        filename: str
    ) -> Path:
        """Download uploaded file"""

        upload = await self.upload_repo.find_by_filename(
            filename
        )

        if not upload:
            raise ResourceNotFoundException("Upload")

        path = Path(upload["filePath"])

        if not path.exists():
            raise ResourceNotFoundException("File")

        logger_upload.info(
            f"Downloaded {filename}"
        )

        return path
    
    async def get_all_uploads(self) -> list:
        """Get all uploads"""

        uploads = await self.upload_repo.get_all_sorted()

        logger_upload.info(
            f"Fetched {len(uploads)} uploads"
        )

        for upload in uploads:
            upload["id"] = str(upload["_id"])
            upload["userId"] = str(upload["userId"])
            upload["projectId"] = str(upload["projectId"])

        return uploads

    async def delete_upload(
        self,
        upload_id: str
    ) -> bool:
        """Delete uploaded file"""

        upload = await self.upload_repo.find_by_id(upload_id)

        if not upload:
            raise ResourceNotFoundException("Upload")

        file_path = Path(upload["filePath"])

        if file_path.exists():
            os.remove(file_path)

        deleted = await self.upload_repo.delete(upload_id)

        if not deleted:
            raise ValidationException(
                "Failed to delete upload."
            )

        await self.activity_service.log_activity(
            user_id="system",
            user_role="system",
            action="Upload Deleted",
            entity="Upload",
            entity_id=upload_id,
            details={
                "fileName": upload["fileName"]
            }
        )

        logger_upload.info(
            f"Upload {upload_id} deleted"
        )

        return True

class BlogService:
    """Blog business logic"""
    
    def __init__(self):
        self.blog_repo = BlogRepository()
        self.activity_service = ActivityLogService()
    
    async def create_blog(
        self,
        current_user: dict,
        title: str,
        slug: str,
        content: str,
        thumbnail: str | None
    ) -> dict:
        """Create blog"""

        title = title.strip()
        slug = slug.strip().lower()
        content = content.strip()

        if await self.blog_repo.slug_exists(slug):
            raise DuplicateException("Slug")

        blog_data = {
            "title": title,
            "slug": slug,
            "content": content,
            "thumbnail": thumbnail,
            "author": current_user["name"],
            "views": 0
        }

        blog_id = await self.blog_repo.create(blog_data)

        created_blog = await self.blog_repo.find_by_id(blog_id)

        created_blog["id"] = str(created_blog["_id"])

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Blog Created",
            entity="Blog",
            entity_id=blog_id
        )

        logger_blog.info(f"Blog created: {slug}")

        return created_blog
    
    async def get_all_blogs(self) -> list:
        """Get all blogs"""

        blogs = await self.blog_repo.get_all_sorted()

        for blog in blogs:
            blog["id"] = str(
                blog["_id"]
            )

        return blogs
    
    async def get_blog_by_slug(
        self,
        slug: str
    ) -> dict:
        """Get blog by slug"""

        blog = await self.blog_repo.find_by_slug(
            slug
        )

        if not blog:
            raise ResourceNotFoundException(
                "Blog"
            )

        await self.blog_repo.increment_views(
            str(blog["_id"])
        )

        blog["views"] += 1
        blog["id"] = str(
            blog["_id"]
        )

        return blog
    
    async def delete_blog(
        self,
        blog_id: str,
        current_user: dict
    ) -> dict:
        """Delete blog"""

        blog = await self.blog_repo.find_by_id(
            blog_id
        )

        if not blog:
            raise ResourceNotFoundException(
                "Blog"
            )

        deleted = await self.blog_repo.delete(
            blog_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete blog."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Blog Deleted",
            entity="Blog",
            entity_id=blog_id
        )

        logger_blog.info(
            f"Blog deleted: {blog_id}"
        )

        return {
            "message": "Blog deleted successfully."
        }

class ContactService:
    """Contact form business logic"""

    def __init__(self):
        self.contact_repo = ContactRepository()
        self.lead_repo = LeadRepository()
        self.user_repo = UserRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()

    async def submit_contact_form(
        self,
        name: str,
        email: str,
        message: str
    ) -> dict:
        """Submit contact form and auto-create CRM lead"""

        name = name.strip()
        email = email.strip().lower()
        message = message.strip()

        contact_data = {
            "name": name,
            "email": email,
            "message": message
        }

        contact_id = await self.contact_repo.create(
            contact_data
        )

        created_contact = await self.contact_repo.find_by_id(
            contact_id
        )

        created_contact["id"] = str(
            created_contact["_id"]
        )

        existing_lead = await self.lead_repo.find_by_email(
            email
        )

        if existing_lead:

            await self.lead_repo.add_history_entry(
                str(existing_lead["_id"]),
                {
                    "action": "Website Contact Form Submitted Again",
                    "message": message,
                    "changedBy": "system"
                }
            )

            await self.activity_service.log_activity(
                user_id="system",
                user_role="system",
                action="Existing Lead Contacted Again",
                entity="Lead",
                entity_id=str(existing_lead["_id"]),
                metadata={
                    "source": "Website Contact Form"
                }
            )

        else:

            lead_data = {
                "companyName": None,
                "contactPerson": name,
                "phone": None,
                "email": email,
                "business": "Website Enquiry",
                "leadSource": "Website Contact Form",
                "notes": message,
                "stage": "New",
                "assignedTo": None,
                "history": []
            }

            lead_id = await self.lead_repo.create(
                lead_data
            )

            await self.activity_service.log_activity(
                user_id="system",
                user_role="system",
                action="Lead Auto Created",
                entity="Lead",
                entity_id=lead_id,
                metadata={
                    "source": "Website Contact Form"
                }
            )

            admins = await self.user_repo.get_by_role(
                "super_admin"
            )

            for admin in admins:
                await self.notification_service.create_notification(
                    user_id=str(admin["_id"]),
                    notif_type="lead",
                    title="New Website Lead",
                    message=f"{name} ({email}) submitted a new website enquiry.",
                    entity_id=lead_id,
                    entity_type="Lead"
                )

        try:
            send_contact_alert(
                name,
                email,
                message
            )
        except Exception as exc:
            logger_contact.error(
                f"Failed to send contact alert: {exc}"
            )

        logger_contact.info(
            f"New contact form submitted by {email}"
        )

        return created_contact

class LeadService:
    """Lead/CRM business logic"""
    
    def __init__(self):
        self.lead_repo = LeadRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()
        self.user_repo = UserRepository()
    
    async def create_lead(
        self,
        current_user: dict,
        company_name: str,
        contact_person: str,
        phone: str,
        email: str,
        business: str,
        lead_source: str = None,
        notes: str = None
    ) -> dict:
        """Create new lead"""

        if await self.lead_repo.find_by_email(email):
            raise DuplicateException(
                "Email already exists as lead."
            )

        company_name = company_name.strip() if company_name else None
        contact_person = contact_person.strip()
        phone = phone.strip() if phone else None
        email = email.strip().lower()
        business = business.strip()
        lead_source = lead_source.strip() if lead_source else None
        notes = notes.strip() if notes else None

        lead_data = {
            "companyName": company_name,
            "contactPerson": contact_person,
            "phone": phone,
            "email": email,
            "business": business,
            "leadSource": lead_source or "Contact Form",
            "notes": notes,
            "stage": "New",
            "history": []
        }

        lead_id = await self.lead_repo.create(
            lead_data
        )

        created_lead = await self.lead_repo.find_by_id(
            lead_id
        )

        created_lead["id"] = str(
            created_lead["_id"]
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Lead Created",
            entity="Lead",
            entity_id=lead_id
        )

        logger_lead.info(
            f"Lead created: {lead_id}"
        )

        return created_lead
        
    async def update_lead(
        self,
        lead_id: str,
        current_user: dict,
        updated_by: str,
        **updates
    ) -> dict:
        """Update lead"""

        lead = await self.lead_repo.find_by_id(
            lead_id
        )

        if not lead:
            raise ResourceNotFoundException(
                "Lead"
            )
        
        # Prevent duplicate email on update
        if "email" in updates:
            updates["email"] = updates["email"].strip().lower()
            existing_lead = await self.lead_repo.find_by_email(
                updates["email"]
            )

            if (
                existing_lead
                and str(existing_lead["_id"]) != lead_id
            ):
                raise DuplicateException(
                    "Email already exists as lead."
                )

        # Track field changes
        for field, new_value in updates.items():
            old_value = lead.get(field)

            if old_value != new_value:
                await self.lead_repo.add_history_entry(
                    lead_id,
                    {
                        "action": "Lead Updated",
                        "field": field,
                        "oldValue": str(old_value) if old_value else None,
                        "newValue": str(new_value) if new_value else None,
                        "changedBy": updated_by
                    }
                )

        updated = await self.lead_repo.update(
            lead_id,
            updates
        )

        if not updated:
            raise ValidationException(
                "Failed to update lead."
            )

        updated_lead = await self.lead_repo.find_by_id(
            lead_id
        )

        updated_lead["id"] = str(
            updated_lead["_id"]
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Lead Updated",
            entity="Lead",
            entity_id=lead_id,
            metadata={
                "updates": updates
            }
        )

        logger_lead.info(
            f"Lead updated: {lead_id}"
        )

        return updated_lead
    
    async def assign_lead(
        self,
        lead_id: str,
        sub_admin_id: str,
        current_user: dict
    ) -> dict:
        """Assign lead to sub-admin"""

        lead = await self.lead_repo.find_by_id(
            lead_id
        )

        if not lead:
            raise ResourceNotFoundException(
                "Lead"
            )

        user = await self.user_repo.find_by_id(
            sub_admin_id
        )

        if not user:
            raise ResourceNotFoundException(
                "User"
            )

        if user["role"] != "sub_admin":
            raise ValidationException(
                "Lead can only be assigned to a Sub Admin."
            )
        
        if lead.get("assignedTo") == sub_admin_id:
            raise ValidationException(
                "Lead is already assigned to this Sub Admin."
            )

        updated = await self.lead_repo.update(
            lead_id,
            {
                "assignedTo": sub_admin_id
            }
        )

        if not updated:
            raise ValidationException(
                "Failed to assign lead."
            )

        updated_lead = await self.lead_repo.find_by_id(
            lead_id
        )

        updated_lead["id"] = str(
            updated_lead["_id"]
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Lead Assigned",
            entity="Lead",
            entity_id=lead_id,
            metadata={
                "assignedTo": sub_admin_id
            }
        )

        await self.notification_service.notify_admins(
            title="Lead Assigned",
            message=f"Lead '{lead.get('companyName') or lead.get('contactPerson')}' assigned to {user.get('name')}.",
            notification_type="lead_assignment"
        )

        logger_lead.info(
            f"Lead {lead_id} assigned to {sub_admin_id}"
        )

        return updated_lead
    
    async def mark_lead_as_won(
        self,
        lead_id: str,
        current_user: dict
    ) -> dict:
        """Mark lead as won"""

        lead = await self.lead_repo.find_by_id(
            lead_id
        )

        if not lead:
            raise ResourceNotFoundException(
                "Lead"
            )

        await self.lead_repo.add_history_entry(
            lead_id,
            {
                "action": "Lead Marked Won",
                "field": "stage",
                "oldValue": lead.get("stage"),
                "newValue": "Won",
                "changedBy": current_user["id"]
            }
        )

        updated = await self.lead_repo.update(
            lead_id,
            {
                "stage": "Won"
            }
        )

        if not updated:
            raise ValidationException(
                "Failed to mark lead as won."
            )

        updated_lead = await self.lead_repo.find_by_id(
            lead_id
        )

        updated_lead["id"] = str(
            updated_lead["_id"]
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Lead Marked Won",
            entity="Lead",
            entity_id=lead_id
        )

        logger_lead.info(
            f"Lead marked as won: {lead_id}"
        )

        return updated_lead

    async def mark_lead_as_lost(
        self,
        lead_id: str,
        current_user: dict
    ) -> dict:
        """Mark lead as lost"""

        lead = await self.lead_repo.find_by_id(
            lead_id
        )

        if not lead:
            raise ResourceNotFoundException(
                "Lead"
            )

        await self.lead_repo.add_history_entry(
            lead_id,
            {
                "action": "Lead Marked Lost",
                "field": "stage",
                "oldValue": lead.get("stage"),
                "newValue": "Lost",
                "changedBy": current_user["id"]
            }
        )

        updated = await self.lead_repo.update(
            lead_id,
            {
                "stage": "Lost"
            }
        )

        if not updated:
            raise ValidationException(
                "Failed to mark lead as lost."
            )

        updated_lead = await self.lead_repo.find_by_id(
            lead_id
        )

        updated_lead["id"] = str(
            updated_lead["_id"]
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Lead Marked Lost",
            entity="Lead",
            entity_id=lead_id
        )

        logger_lead.info(
            f"Lead marked as lost: {lead_id}"
        )

        return updated_lead

    async def get_all_leads(
        self,
        skip: int = 0,
        limit: int = 100,
        stage: str = None
    ) -> list:
        """Get all leads"""

        if stage:
            leads = await self.lead_repo.find_by_stage(
                stage,
                skip,
                limit
            )
        else:
            leads = await self.lead_repo.get_all_sorted(
                skip,
                limit
            )

        for lead in leads:
            lead["id"] = str(
                lead["_id"]
            )

        return leads

    async def get_lead(
        self,
        lead_id: str
    ) -> dict:
        """Get lead details"""

        lead = await self.lead_repo.find_by_id(
            lead_id
        )

        if not lead:
            raise ResourceNotFoundException(
                "Lead"
            )

        lead["id"] = str(
            lead["_id"]
        )

        return lead

    async def get_lead_history(
        self,
        lead_id: str
    ) -> list:
        """Get lead history"""

        lead = await self.lead_repo.find_by_id(
            lead_id
        )

        if not lead:
            raise ResourceNotFoundException(
                "Lead"
            )

        return lead.get(
            "history",
            []
        )

class RequirementService:
    """Requirements documentation service"""

    def __init__(self):
        self.req_repo = RequirementRepository()
        self.lead_repo = LeadRepository()
        self.project_repo = ProjectRepository()
        self.quotation_repo = QuotationRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()

    async def create_requirement(
        self,
        current_user: dict,
        lead_id: str = None,
        project_id: str = None,
        created_by: str = None,
        **req_data
    ) -> dict:
        """Create requirement documentation"""

        if not lead_id and not project_id:
            raise ValidationException(
                "Either lead_id or project_id must be provided."
            )

        if lead_id:
            lead = await self.lead_repo.find_by_id(
                lead_id
            )

            if not lead:
                raise ResourceNotFoundException(
                    "Lead"
                )

            if await self.req_repo.exists_by_lead(
                lead_id
            ):
                raise DuplicateException(
                    "Requirement already exists for this lead."
                )

        if project_id:
            project = await self.project_repo.find_by_id(
                project_id
            )

            if not project:
                raise ResourceNotFoundException(
                    "Project"
                )

            if await self.req_repo.exists_by_project(
                project_id
            ):
                raise DuplicateException(
                    "Requirement already exists for this project."
                )

        req_data["leadId"] = lead_id
        req_data["projectId"] = project_id

        req_data["status"] = RequirementStatus.PENDING.value
        req_data["approvedBy"] = None
        req_data["approvedAt"] = None
        req_data["remarks"] = None
        req_data["lastUpdatedBy"] = created_by
        req_data["lastUpdatedAt"] = datetime.utcnow()

        req_id = await self.req_repo.create(
            req_data
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Requirement Created",
            entity="Requirement",
            entity_id=req_id
        )

        logger_requirement.info(
            f"Requirement created: {req_id}"
        )

        created_req = await self.req_repo.find_by_id(
            req_id
        )

        created_req["id"] = str(created_req["_id"])

        return created_req

    async def update_requirement(
        self,
        requirement_id: str,
        current_user: dict,
        updated_by: str,
        **updates
    ) -> dict:
        """Update requirement"""

        req = await self.req_repo.find_by_id(
            requirement_id
        )

        if not req:
            raise ResourceNotFoundException(
                "Requirement"
            )

        if req.get("status") == RequirementStatus.APPROVED.value:
            raise ValidationException(
                "Approved requirement cannot be edited. Request changes first."
            )

        updates["status"] = RequirementStatus.PENDING.value
        updates["lastUpdatedBy"] = updated_by
        updates["lastUpdatedAt"] = datetime.utcnow()

        updated = await self.req_repo.update(
            requirement_id,
            updates
        )

        if not updated:
            raise ValidationException(
                "Failed to update requirement."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Requirement Updated",
            entity="Requirement",
            entity_id=requirement_id
        )

        logger_requirement.info(
            f"Requirement updated: {requirement_id}"
        )

        updated_req = await self.req_repo.find_by_id(
            requirement_id
        )

        updated_req["id"] = str(
            updated_req["_id"]
        )

        return updated_req

    async def approve_requirement(
        self,
        requirement_id: str,
        current_user: dict,
        approved_by: str,
        remarks: str = None
    ) -> dict:
        """Approve requirement"""

        req = await self.req_repo.find_by_id(
            requirement_id
        )

        if not req:
            raise ResourceNotFoundException(
                "Requirement"
            )

        if req.get("status") == RequirementStatus.APPROVED.value:
            raise ValidationException(
                "Requirement is already approved."
            )

        updated = await self.req_repo.update(
            requirement_id,
            {
                "status": RequirementStatus.APPROVED.value,
                "approvedBy": approved_by,
                "approvedAt": datetime.utcnow(),
                "remarks": remarks
            }
        )

        if not updated:
            raise ValidationException(
                "Failed to approve requirement."
            )

        quotation = None

        if req.get("leadId"):
            quotation = await self.quotation_repo.find_one(
                {
                    "leadId": req["leadId"]
                }
            )

        elif req.get("projectId"):
            quotation = await self.quotation_repo.find_one(
                {
                    "projectId": req["projectId"]
                }
            )

        if quotation:
            await self.quotation_repo.update(
                str(quotation["_id"]),
                {
                    "status": "Revision Requested"
                }
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Requirement Approved",
            entity="Requirement",
            entity_id=requirement_id
        )

        logger_requirement.info(
            f"Requirement approved: {requirement_id}"
        )

        approved_req = await self.req_repo.find_by_id(
            requirement_id
        )

        approved_req["id"] = str(
            approved_req["_id"]
        )

        return approved_req

    async def request_changes(
        self,
        requirement_id: str,
        current_user: dict,
        remarks: str
    ) -> dict:
        """Request requirement changes"""

        req = await self.req_repo.find_by_id(
            requirement_id
        )

        if not req:
            raise ResourceNotFoundException(
                "Requirement"
            )

        if req.get("status") == RequirementStatus.CHANGES_REQUESTED.value:
            raise ValidationException(
                "Changes have already been requested."
            )

        updated = await self.req_repo.update(
            requirement_id,
            {
                "status": "CHANGES_REQUESTED",
                "remarks": remarks
            }
        )

        if not updated:
            raise ValidationException(
                "Failed to request requirement changes."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Requirement Changes Requested",
            entity="Requirement",
            entity_id=requirement_id
        )

        logger_requirement.info(
            f"Changes requested for requirement: {requirement_id}"
        )

        updated_req = await self.req_repo.find_by_id(
            requirement_id
        )

        updated_req["id"] = str(
            updated_req["_id"]
        )

        return updated_req

    async def get_requirement(
        self,
        requirement_id: str
    ) -> dict:
        """Get requirement details"""

        requirement = await self.req_repo.find_by_id(
            requirement_id
        )

        if not requirement:
            raise ResourceNotFoundException(
                "Requirement"
            )

        requirement["id"] = str(
            requirement["_id"]
        )

        return requirement

    async def delete_requirement(
        self,
        requirement_id: str,
        current_user: dict
    ) -> dict:
        """Delete requirement"""

        requirement = await self.req_repo.find_by_id(
            requirement_id
        )

        if not requirement:
            raise ResourceNotFoundException(
                "Requirement"
            )

        deleted = await self.req_repo.delete(
            requirement_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete requirement."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Requirement Deleted",
            entity="Requirement",
            entity_id=requirement_id
        )

        logger_requirement.info(
            f"Requirement deleted: {requirement_id}"
        )

        return {
            "message": "Requirement deleted successfully."
        }

    async def get_lead_requirements(
        self,
        lead_id: str
    ) -> dict:
        """Get requirements for lead"""

        requirement = await self.req_repo.find_by_lead(
            lead_id
        )

        if not requirement:
            raise ResourceNotFoundException(
                "Requirement"
            )

        requirement["id"] = str(
            requirement["_id"]
        )

        return requirement

    async def get_project_requirements(
        self,
        project_id: str
    ) -> dict:
        """Get requirements for project"""

        requirement = await self.req_repo.find_by_project(
            project_id
        )

        if not requirement:
            raise ResourceNotFoundException(
                "Requirement"
            )

        requirement["id"] = str(
            requirement["_id"]
        )

        return requirement

class QuotationService:
    """Quotation management service"""
    
    def __init__(self):
        self.lead_repo = LeadRepository()
        self.project_repo = ProjectRepository()
        self.quotation_repo = QuotationRepository()
        self.notification_service = NotificationService()
        self.user_repo = UserRepository()
        self.req_repo = RequirementRepository()
        self.project_service = ProjectService()
        self.lead_service = LeadService()
        self.timeline_service = TimelineService()
        self.discussion_service = DiscussionService()
        self.activity_service = ActivityLogService()
    
    async def create_quotation(self, client_id: str, services: list, items: list, 
                               timeline: str, validity: int, terms: str,
                               lead_id: str = None, project_id: str = None, notes: str = None) -> dict:
        """Create new quotation"""
        # Validate Client
        client = await self.user_repo.find_by_id(client_id)

        if not client:
            raise ResourceNotFoundException("Client")

        # Validate Lead
        if lead_id:

            lead = await self.lead_repo.find_by_id(lead_id)

            if not lead:
                raise ResourceNotFoundException("Lead")

        # Validate Project
        if project_id:

            project = await self.project_repo.find_by_id(project_id)

            if not project:
                raise ResourceNotFoundException("Project")
            
        requirement = None

        if lead_id:
            requirement = await self.req_repo.find_by_lead(lead_id)

        elif project_id:
            requirement = await self.req_repo.find_by_project(project_id)

        if not requirement:
            raise ValidationException(
                "Requirement must be created before creating quotation."
            )

        if requirement.get("status") != RequirementStatus.APPROVED.value:
            raise ValidationException(
                "Requirement must be approved before quotation can be created."
            )
        
        if lead_id:
            existing = await self.quotation_repo.find_by_lead(
                lead_id
            )

            if existing:
                raise DuplicateException(
                    "Quotation already exists for this lead."
                )

        elif project_id:
            existing = await self.quotation_repo.find_by_project(
                project_id
            )

            if existing:
                raise DuplicateException(
                    "Quotation already exists for this project."
                )
        
        
        total_amount = sum(item.get("total", 0) for item in items)
        
        quotation_data = {
            "clientId": client_id,
            "leadId": lead_id,
            "projectId": project_id,
            "quotationNumber": await self.quotation_repo.get_next_quotation_number(),
            "services": services,
            "items": items,
            "timeline": timeline,
            "validity": validity,
            "terms": terms,
            "notes": notes,
            "status": QuotationStatus.DRAFT,
            "totalAmount": total_amount,
            # Revision tracking
            "revisionCount": 0,
            "lastRevisedBy": None,
            "lastRevisedAt": None
            }
        
        quotation_id = await self.quotation_repo.create(
            quotation_data
        )

        created_quotation = await self.quotation_repo.find_by_id(
            quotation_id
        )

        created_quotation["id"] = str(
            created_quotation["_id"]
        )

        logger_quotation.info(
            f"Quotation created: {quotation_id}"
        )

        return created_quotation
    
    async def update_quotation_status(self, quotation_id: str, status: str, user_id: str = None) -> dict:
        """Update quotation status"""
        valid_statuses = [
            status.value
            for status in QuotationStatus
        ]
        if status not in valid_statuses:
            raise ValidationException(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        quotation = await self.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise ResourceNotFoundException("Quotation")
        
        updated = await self.quotation_repo.update(quotation_id, {"status": status})
        if not updated:
            raise ValidationException(
                "Failed to update quotation."
            )
        # Business workflow
        if quotation.get("leadId"):

            if status == QuotationStatus.ACCEPTED.value:

                await self.lead_service.mark_lead_as_won(
                    quotation["leadId"],
                    user_id or "system"
                )

            elif status == QuotationStatus.REJECTED.value:

                await self.lead_service.mark_lead_as_lost(
                    quotation["leadId"],
                    user_id or "system"
                )
        
        updated = await self.quotation_repo.find_by_id(quotation_id)
        updated["id"] = str(updated["_id"])

        logger_quotation.info(
            f"Quotation {quotation_id} status changed to {status}"
        )
        
        return updated
    
    async def update_quotation(
        self,
        quotation_id: str,
        revised_by: str,
        **updates
    ) -> dict:
        """
        Update existing quotation after requirement revision
        """

        quotation = await self.quotation_repo.find_by_id(quotation_id)

        if not quotation:
            raise ResourceNotFoundException("Quotation")

        # Accepted quotation cannot be revised
        if quotation.get("status") == QuotationStatus.ACCEPTED.value:
            raise ValidationException(
                "Accepted quotation cannot be revised."
            )
        
        # Rejected quotation cannot be revised
        if quotation.get("status") == QuotationStatus.REJECTED.value:
            raise ValidationException(
                "Rejected quotation cannot be revised."
            )

        # Recalculate total amount if items updated
        if "items" in updates:

            updates["totalAmount"] = sum(
                item.get("total", 0)
                for item in updates["items"]
            )

        updates["status"] = QuotationStatus.DRAFT.value

        updates["revisionCount"] = quotation.get(
            "revisionCount",
            0
        ) + 1

        updates["lastRevisedBy"] = revised_by

        updates["lastRevisedAt"] = datetime.utcnow()

        updated = await self.quotation_repo.update(
            quotation_id,
            updates
        )

        if not updated:
            raise ValidationException(
                "Failed to update quotation."
            )

        updated = await self.quotation_repo.find_by_id(
            quotation_id
        )

        updated["id"] = str(updated["_id"])

        user = await self.user_repo.find_by_id(revised_by)
        user_role = user.get("role") if user else "System"

        await self.activity_service.log_activity(
            user_id=revised_by,
            user_role=user_role,
            action="Quotation Revised",
            entity="Quotation",
            entity_id=quotation_id,
            details={
                "revisionCount": updated.get("revisionCount", 0)
            }
        )

        logger_quotation.info(
            f"Quotation updated: {quotation_id}"
        )

        return updated
    
    async def send_quotation(
        self,
        quotation_id: str,
        current_user: dict
    ) -> dict:
        """
        Send quotation to client.
        """

        quotation = await self.quotation_repo.find_by_id(
            quotation_id
        )

        if not quotation:
            raise ResourceNotFoundException("Quotation")

        if quotation.get("status") == QuotationStatus.SENT.value:
            raise ValidationException(
                "Quotation has already been sent."
            )

        updated = await self.update_quotation_status(
            quotation_id=quotation_id,
            status=QuotationStatus.SENT.value,
            user_id=current_user["id"]
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Quotation Sent",
            entity="Quotation",
            entity_id=quotation_id,
            details={
                "quotationNumber": quotation["quotationNumber"]
            }
        )

        await self.notification_service.create_notification(
            user_id=str(quotation["clientId"]),
            notif_type="quotation",
            title="Quotation Sent",
            message=f"Quotation {quotation['quotationNumber']} has been sent.",
            entity_id=quotation_id,
            entity_type="Quotation"
        )

        logger_quotation.info(
            f"Quotation {quotation['quotationNumber']} sent successfully."
        )

        return updated
    
    async def accept_quotation(
        self,
        quotation_id: str,
        user_id: str
    ):
        """
        Accept quotation and start project workflow
        """

        quotation = await self.quotation_repo.find_by_id(quotation_id)

        if not quotation:
            raise ResourceNotFoundException("Quotation")

        if quotation.get("status") == QuotationStatus.ACCEPTED.value:
            raise PermissionException("Quotation already accepted")

        # Requirement Approval Check
        if quotation.get("leadId"):

            requirement = await self.req_repo.find_by_lead(
                quotation["leadId"]
            )

            if not requirement:
                raise PermissionException(
                    "Requirement not found"
                )

            if requirement.get("status") != RequirementStatus.APPROVED.value:
                raise PermissionException(
                    "Requirement must be approved before accepting quotation."
                )

        # Update quotation status

        # Update quotation status and trigger business workflow
        quotation = await self.update_quotation_status(
            quotation_id=quotation_id,
            status=QuotationStatus.ACCEPTED.value,
            user_id=user_id
        )

        # Create Project
        project = await self.project_service.create_project_from_quotation(
            quotation
        )

        # Initialize default timeline
        await self.timeline_service.initialize_project_timeline(
            project_id=project["id"],
            created_by=user_id
        )

        # Initialize project discussion
        await self.discussion_service.initialize_project_discussion(
            project_id=project["id"],
            created_by=user_id
        )

        # Log activity
        await self.activity_service.log_activity(
            user_id=user_id,
            user_role="client",
            action="Quotation Accepted",
            entity="Quotation",
            entity_id=quotation_id,
            details={
                "projectId": project["id"]
            }
        )

        # Notify Super Admin(s)
        admins = await self.user_repo.get_by_role("super_admin")

        for admin in admins:
            await self.notification_service.create_notification(
                user_id=str(admin["_id"]),
                notif_type="quotation",
                title="Quotation Accepted",
                message=f"Quotation {quotation['quotationNumber']} has been accepted.",
                entity_id=quotation_id,
                entity_type="Quotation"
            )

        logger_quotation.info(
            f"Quotation accepted: {quotation_id}"
        )

        return {
            "quotation": quotation,
            "project": project
        }

    async def get_quotations(
        self,
        current_user: dict,
        skip: int = 0,
        limit: int = 100,
        status: str = None
    ) -> list:
        """Get quotations"""

        if current_user["role"] == "client":
            quotations = await self.quotation_repo.find_by_client(
                current_user["id"],
                skip,
                limit
            )

        elif current_user["role"] in ["super_admin", "sub_admin"]:

            if status:
                quotations = await self.quotation_repo.find_by_status(
                    status,
                    skip,
                    limit
                )
            else:
                quotations = await self.quotation_repo.get_all_sorted(
                    skip,
                    limit
                )

        else:
            raise PermissionException("Access denied")

        for quotation in quotations:
            quotation["id"] = str(quotation["_id"])

        logger_quotation.info(
            f"Fetched {len(quotations)} quotations"
        )

        return quotations
    
    async def get_quotation(
        self,
        quotation_id: str,
        current_user: dict
    ) -> dict:
        """Get quotation"""

        quotation = await self.quotation_repo.find_by_id(
            quotation_id
        )

        if not quotation:
            raise ResourceNotFoundException("Quotation")

        if (
            current_user["role"] == "client"
            and str(quotation["clientId"]) != current_user["id"]
        ):
            raise PermissionException("Access denied")

        quotation["id"] = str(quotation["_id"])

        return quotation
    
    async def reject_quotation(
        self,
        quotation_id: str,
        current_user: dict
    ):
        """Reject quotation"""

        await self.get_quotation(
            quotation_id,
            current_user
        )

        return await self.update_quotation_status(
            quotation_id,
            QuotationStatus.REJECTED.value,
            current_user["id"]
        )
    
    async def request_revision(
        self,
        quotation_id: str,
        current_user: dict
    ):
        """Request quotation revision"""

        await self.get_quotation(
            quotation_id,
            current_user
        )

        return await self.update_quotation_status(
            quotation_id,
            QuotationStatus.REVISION_REQUESTED.value,
            current_user["id"]
        )

    async def delete_quotation(
        self,
        quotation_id: str,
        current_user: dict
    ):
        """Delete quotation"""

        quotation = await self.quotation_repo.find_by_id(
            quotation_id
        )

        if not quotation:
            raise ResourceNotFoundException("Quotation")

        deleted = await self.quotation_repo.delete(
            quotation_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete quotation."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Quotation Deleted",
            entity="Quotation",
            entity_id=quotation_id
        )

        logger_quotation.info(
            f"Quotation deleted: {quotation_id}"
        )

        return {
            "message": "Quotation deleted successfully."
        }

class TimelineService:
    """Project timeline service"""

    def __init__(self):
        self.timeline_repo = TimelineRepository()
        self.project_repo = ProjectRepository()
        self.project_service = ProjectService()
        self.activity_service = ActivityLogService()

    async def add_timeline_event(
        self,
        project_id: str,
        title: str,
        created_by: str,
        description: str = None
    ) -> dict:
        """Add timeline event"""

        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException("Project")

        event_data = {
            "projectId": project_id,
            "title": title,
            "description": description,
            "createdBy": created_by
        }

        event_id = await self.timeline_repo.create(
            event_data
        )

        user = await self.user_repo.find_by_id(created_by)

        user_role = user.get("role") if user else "system"

        await self.activity_service.log_activity(
            user_id=created_by,
            user_role=user_role,
            action="Timeline Event Added",
            entity="Project",
            entity_id=project_id,
            details={
                "event": title
            }
        )

        # Synchronize project status from timeline
        normalized_title = title.strip().lower()

        status_mapping = {
            "project started": "in_progress",
            "testing started": "testing",
            "deployment started": "deployment",
            "project delivered": "delivered",
            "project completed": "completed"
        }

        if normalized_title in status_mapping:
            await self.project_service.update_status(
                project_id,
                status_mapping[normalized_title]
            )

        event = await self.timeline_repo.find_by_id(
            event_id
        )

        event["id"] = str(event["_id"])

        logger_timeline.info(
            f"Timeline event '{title}' added for project {project_id}"
        )

        return event

    async def get_project_timeline(
        self,
        project_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get timeline for project"""

        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException("Project")

        events = await self.timeline_repo.find_by_project(
            project_id,
            skip,
            limit
        )

        for event in events:
            event["id"] = str(event["_id"])

        return events

    async def initialize_project_timeline(
        self,
        project_id: str,
        created_by: str
    ):
        """Initialize default timeline for newly created project"""

        await self.add_timeline_event(
            project_id=project_id,
            title="Project Created",
            description="Project created after quotation acceptance.",
            created_by=created_by
        )

        await self.add_timeline_event(
            project_id=project_id,
            title="Project Started",
            description="Project has entered development workflow.",
            created_by=created_by
        )

        logger_timeline.info(
            f"Default timeline initialized for project {project_id}"
        )

    async def delete_timeline_event(
        self,
        event_id: str,
        current_user: dict
    ):
        """Delete timeline event"""

        event = await self.timeline_repo.find_by_id(
            event_id
        )

        if not event:
            raise ResourceNotFoundException(
                "Timeline Event"
            )

        deleted = await self.timeline_repo.delete(
            event_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete timeline event."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Timeline Event Deleted",
            entity="Timeline Event",
            entity_id=event_id
        )

        logger_timeline.info(
            f"Timeline event deleted: {event_id}"
        )

        return {
            "message": "Timeline event deleted successfully."
        }

class DiscussionService:
    """Project discussion/messaging service"""

    def __init__(self):
        self.discussion_repo = DiscussionRepository()
        self.project_repo = ProjectRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()

    async def add_message(
        self,
        project_id: str,
        current_user: dict,
        author_id: str,
        author_name: str,
        message: str,
        attachments: list = None
    ) -> dict:
        """Add message to project discussion"""

        project = await self.project_repo.find_by_id(
            project_id
        )

        if not project:
            raise ResourceNotFoundException("Project")

        if (
            current_user["role"] == "client"
            and str(project["userId"]) != current_user["id"]
        ):
            raise PermissionException(
                "Access denied"
            )

        msg_data = {
            "projectId": project_id,
            "authorId": author_id,
            "authorName": author_name.strip(),
            "message": message.strip(),
            "attachments": attachments or [],
            "edited": False,
            "seen": False,
            "replies": []
        }

        msg_id = await self.discussion_repo.create(
            msg_data
        )

        await self.activity_service.log_activity(
            user_id=author_id,
            user_role=current_user["role"],
            action="Discussion Message Added",
            entity="Project",
            entity_id=project_id
        )

        message_doc = await self.discussion_repo.find_by_id(
            msg_id
        )

        message_doc["id"] = str(message_doc["_id"])

        logger_discussion.info(
            f"New discussion message added to project {project_id}"
        )

        return message_doc

    async def add_reply(
        self,
        message_id: str,
        current_user: dict,
        author_id: str,
        author_name: str,
        message: str,
        attachments: list = None
    ) -> dict:
        """Add reply to discussion message"""

        discussion = await self.discussion_repo.find_by_id(
            message_id
        )

        if not discussion:
            raise ResourceNotFoundException(
                "Discussion Message"
            )

        project = await self.project_repo.find_by_id(
            str(discussion["projectId"])
        )

        if not project:
            raise ResourceNotFoundException(
                "Project"
            )

        if (
            current_user["role"] == "client"
            and str(project["userId"]) != current_user["id"]
        ):
            raise PermissionException(
                "Access denied"
            )

        reply_data = {
            "messageId": message_id,
            "authorId": author_id,
            "authorName": author_name.strip(),
            "message": message.strip(),
            "attachments": attachments or [],
            "edited": False
        }

        updated = await self.discussion_repo.add_reply(
            message_id,
            reply_data
        )

        if not updated:
            raise ValidationException(
                "Failed to add reply."
            )

        await self.activity_service.log_activity(
            user_id=author_id,
            user_role=current_user["role"],
            action="Discussion Reply Added",
            entity="Discussion",
            entity_id=message_id
        )

        logger_discussion.info(
            f"Reply added to message {message_id}"
        )

        return {
            "message": "Reply added successfully."
        }

    async def get_project_discussion(
        self,
        project_id: str,
        current_user: dict,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get all discussion messages for project"""

        project = await self.project_repo.find_by_id(
            project_id
        )

        if not project:
            raise ResourceNotFoundException("Project")

        if (
            current_user["role"] == "client"
            and str(project["userId"]) != current_user["id"]
        ):
            raise PermissionException(
                "Access denied"
            )

        messages = await self.discussion_repo.find_by_project(
            project_id,
            skip,
            limit
        )

        for message in messages:
            message["id"] = str(message["_id"])

        return messages

    async def initialize_project_discussion(
        self,
        project_id: str,
        created_by: str = "system"
    ):
        """Initialize discussion thread for new project"""

        msg_data = {
            "projectId": project_id,
            "authorId": created_by,
            "authorName": "System",
            "message": (
                "Project discussion has been initialized. "
                "All future communication regarding this project "
                "will happen here."
            ),
            "attachments": [],
            "edited": False,
            "seen": False,
            "replies": []
        }

        await self.discussion_repo.create(msg_data)

        logger_discussion.info(
            f"Discussion initialized for project {project_id}"
        )

    async def get_message(
        self,
        message_id: str,
        current_user: dict
    ):
        """Get discussion message"""

        message = await self.discussion_repo.find_by_id(
            message_id
        )

        if not message:
            raise ResourceNotFoundException(
                "Discussion Message"
            )

        project = await self.project_repo.find_by_id(
            str(message["projectId"])
        )

        if (
            current_user["role"] == "client"
            and str(project["userId"]) != current_user["id"]
        ):
            raise PermissionException(
                "Access denied"
            )

        await self.discussion_repo.mark_seen(
            message_id
        )

        message["seen"] = True
        message["id"] = str(message["_id"])

        return message
    
    async def delete_message(
        self,
        message_id: str,
        current_user: dict
    ):
        """Delete discussion message"""

        message = await self.discussion_repo.find_by_id(
            message_id
        )

        if not message:
            raise ResourceNotFoundException(
                "Discussion Message"
            )

        if (
            current_user["role"] != "super_admin"
            and str(message["authorId"]) != current_user["id"]
        ):
            raise PermissionException(
                "Access denied"
            )

        deleted = await self.discussion_repo.delete(
            message_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete message."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Discussion Message Deleted",
            entity="Discussion",
            entity_id=message_id
        )

        logger_discussion.info(
            f"Discussion message deleted: {message_id}"
        )

        return {
            "message": "Message deleted successfully."
        }

class DeliverablesService:
    """Deliverables management service"""

    def __init__(self):
        self.deliverables_repo = DeliverablesRepository()
        self.project_repo = ProjectRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()
        self.user_repo = UserRepository()

    async def create_deliverables(
        self,
        project_id: str,
        current_user: dict,
        **deliverables_data
    ) -> dict:
        """Create deliverables for project"""

        project = await self.project_repo.find_by_id(
            project_id
        )

        if not project:
            raise ResourceNotFoundException("Project")

        if project.get("status") not in [
            "in_progress",
            "testing",
            "deployment"
        ]:
            raise ValidationException(
                "Deliverables can only be created for active projects."
            )

        if await self.deliverables_repo.exists_by_project(project_id):
            raise ValidationException(
                "Deliverables already exist for this project."
            )

        deliverables_data["projectId"] = project_id

        del_id = await self.deliverables_repo.create(
            deliverables_data
        )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Deliverables Created",
            entity="Project",
            entity_id=project_id
        )

        admins = await self.user_repo.get_by_role(
            "super_admin"
        )

        for admin in admins:
            await self.notification_service.create_notification(
                user_id=str(admin["_id"]),
                notif_type="deliverables",
                title="Deliverables Created",
                message=f"Deliverables created for project {project_id}.",
                entity_id=del_id,
                entity_type="Deliverables"
            )

        deliverable = await self.deliverables_repo.find_by_id(
            del_id
        )

        deliverable["id"] = str(deliverable["_id"])

        logger_deliverables.info(
            f"Deliverables created for project {project_id}"
        )

        return deliverable

    async def update_deliverables(
        self,
        project_id: str,
        current_user: dict,
        **updates
    ) -> dict:
        """Update project deliverables"""

        project = await self.project_repo.find_by_id(
            project_id
        )

        if not project:
            raise ResourceNotFoundException("Project")

        deliverable = await self.deliverables_repo.find_by_project(
            project_id
        )

        if not deliverable:
            raise ResourceNotFoundException(
                "Deliverables"
            )

        updated = await self.deliverables_repo.update(
            str(deliverable["_id"]),
            updates
        )

        if not updated:
            raise ValidationException(
                "Failed to update deliverables."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Deliverables Updated",
            entity="Project",
            entity_id=project_id
        )

        updated_deliverable = await self.deliverables_repo.find_by_project(
            project_id
        )

        updated_deliverable["id"] = str(
            updated_deliverable["_id"]
        )

        logger_deliverables.info(
            f"Deliverables updated for project {project_id}"
        )

        return updated_deliverable

    async def get_deliverables(
        self,
        project_id: str,
        current_user: dict
    ) -> dict:
        """Get project deliverables"""

        project = await self.project_repo.find_by_id(
            project_id
        )

        if not project:
            raise ResourceNotFoundException(
                "Project"
            )

        if (
            current_user["role"] == "client"
            and str(project["userId"]) != current_user["id"]
        ):
            raise PermissionException(
                "Access denied"
            )

        deliverable = await self.deliverables_repo.find_by_project(
            project_id
        )

        if not deliverable:
            raise ResourceNotFoundException(
                "Deliverables"
            )

        deliverable["id"] = str(
            deliverable["_id"]
        )

        return deliverable

    async def delete_deliverables(
        self,
        project_id: str,
        current_user: dict
    ) -> dict:
        """Delete project deliverables"""

        project = await self.project_repo.find_by_id(
            project_id
        )

        if not project:
            raise ResourceNotFoundException(
                "Project"
            )

        deliverable = await self.deliverables_repo.find_by_project(
            project_id
        )

        if not deliverable:
            raise ResourceNotFoundException(
                "Deliverables"
            )

        deleted = await self.deliverables_repo.delete(
            str(deliverable["_id"])
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete deliverables."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Deliverables Deleted",
            entity="Project",
            entity_id=project_id
        )

        logger_deliverables.info(
            f"Deliverables deleted for project {project_id}"
        )

        return {
            "message": "Deliverables deleted successfully."
        }

class ActivityLogService:
    """Activity logging service"""

    def __init__(self):
        self.activity_repo = ActivityLogRepository()

    async def log_activity(
        self,
        user_id: str,
        user_role: str,
        action: str,
        entity: str,
        entity_id: str,
        details: dict = None
    ) -> dict:
        """Log user activity"""

        log_data = {
            "userId": user_id,
            "userRole": user_role,
            "action": action.strip(),
            "entity": entity.strip(),
            "entityId": entity_id,
            "details": details or {}
        }

        log_id = await self.activity_repo.create(
            log_data
        )

        created = await self.activity_repo.find_by_id(
            log_id
        )

        created["id"] = str(created["_id"])

        logger_activity.info(
            f"{action} | {entity} | {entity_id}"
        )

        return created

    async def get_all_logs(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get all activity logs"""

        logs = await self.activity_repo.get_all_sorted(
            skip,
            limit
        )

        for log in logs:
            log["id"] = str(log["_id"])

        return logs

    async def get_user_activity_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get activity logs for a user"""

        if not user_id:
            raise ValidationException(
                "User ID is required."
            )

        logs = await self.activity_repo.find_by_user(
            user_id,
            skip,
            limit
        )

        for log in logs:
            log["id"] = str(log["_id"])

        return logs

    async def get_activity_log(
        self,
        log_id: str
    ) -> dict:
        """Get activity log"""

        log = await self.activity_repo.find_by_id(
            log_id
        )

        if not log:
            raise ResourceNotFoundException(
                "Activity Log"
            )

        log["id"] = str(log["_id"])

        return log

    async def get_entity_history(
        self,
        entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get activity history for entity"""

        if not entity_id:
            raise ValidationException(
                "Entity ID is required."
            )

        logs = await self.activity_repo.find_by_entity(
            entity_id,
            skip,
            limit
        )

        for log in logs:
            log["id"] = str(log["_id"])

        return logs

class NotificationService:
    """Notification management service"""

    def __init__(self):
        self.notification_repo = NotificationRepository()

    async def create_notification(
        self,
        user_id: str,
        notif_type: str,
        title: str,
        message: str,
        entity_id: str = None,
        entity_type: str = None
    ) -> dict:
        """Create notification for user"""

        notif_data = {
            "userId": user_id,
            "type": notif_type,
            "title": title.strip(),
            "message": message.strip(),
            "entityId": entity_id,
            "entityType": entity_type,
            "read": False
        }

        notif_id = await self.notification_repo.create(
            notif_data
        )

        created = await self.notification_repo.find_by_id(
            notif_id
        )

        created["id"] = str(created["_id"])

        logger_notification.info(
            f"Notification created for user {user_id}"
        )

        return created

    async def get_unread_notifications(
        self,
        user_id: str
    ) -> list:
        """Get unread notifications"""

        notifications = await self.notification_repo.find_unread_by_user(
            user_id
        )

        for notification in notifications:
            notification["id"] = str(
                notification["_id"]
            )

        return notifications

    async def get_user_notifications(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get notifications for user"""

        if not user_id:
            raise ValidationException(
                "User ID is required."
            )

        notifications = await self.notification_repo.find_by_user(
            user_id,
            skip,
            limit
        )

        for notif in notifications:
            notif["id"] = str(notif["_id"])

        return notifications

    async def mark_as_read(
        self,
        notification_id: str,
        current_user: dict
    ) -> dict:
        """Mark notification as read"""

        notification = await self.notification_repo.find_by_id(
            notification_id
        )

        if not notification:
            raise ResourceNotFoundException(
                "Notification"
            )

        if str(notification["userId"]) != current_user["id"]:
            raise AuthenticationException(
                "Access denied."
            )

        updated = await self.notification_repo.mark_as_read(
            notification_id
        )

        if not updated:
            raise ValidationException(
                "Failed to mark notification as read."
            )

        notification["read"] = True
        notification["id"] = str(notification["_id"])

        logger_notification.info(
            f"Notification {notification_id} marked as read."
        )

        return notification

    async def mark_all_as_read(
        self,
        user_id: str
    ) -> int:
        """Mark all notifications as read"""

        if not user_id:
            raise ValidationException(
                "User ID is required."
            )

        count = await self.notification_repo.mark_all_as_read(
            user_id
        )

        logger_notification.info(
            f"{count} notifications marked as read for user {user_id}"
        )

        return count

    async def delete_notification(
        self,
        notification_id: str,
        current_user: dict
    ) -> dict:
        """Delete notification"""

        notification = await self.notification_repo.find_by_id(
            notification_id
        )

        if not notification:
            raise ResourceNotFoundException(
                "Notification"
            )

        if str(notification["userId"]) != current_user["id"]:
            raise AuthenticationException(
                "Access denied."
            )

        deleted = await self.notification_repo.delete(
            notification_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete notification."
            )

        logger_notification.info(
            f"Notification {notification_id} deleted."
        )

        return {
            "message": "Notification deleted successfully."
        }

    async def clear_all_notifications(
        self,
        user_id: str
    ) -> dict:
        """Delete all notifications"""

        if not user_id:
            raise ValidationException(
                "User ID is required."
            )

        deleted_count = await self.notification_repo.delete_many_by_user(
            user_id
        )

        logger_notification.info(
            f"{deleted_count} notifications deleted for user {user_id}"
        )

        return {
            "message": f"Deleted {deleted_count} notifications."
        }

class PortfolioService:
    """Portfolio CMS service"""

    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.activity_service = ActivityLogService()

    async def create_portfolio_item(
        self,
        current_user: dict,
        title: str,
        slug: str,
        category: str,
        description: str,
        tech_stack: list,
        website_url: str = None,
        github_url: str = None,
        images: list = None,
        featured: bool = False,
        display_order: int = 0,
        published: bool = True
    ) -> dict:
        """Create portfolio item"""

        slug = slug.strip().lower()

        if not slug:
            raise ValidationException(
                "Slug cannot be empty."
            )

        if await self.portfolio_repo.find_by_slug(slug):
            raise DuplicateException("Slug")

        item_data = {
            "title": title.strip(),
            "slug": slug,
            "category": category.strip().lower(),
            "description": description.strip(),
            "techStack": tech_stack,
            "websiteUrl": website_url,
            "githubUrl": github_url,
            "images": images or [],
            "featured": featured,
            "displayOrder": display_order,
            "published": published
        }

        item_id = await self.portfolio_repo.create(item_data)

        created_item = await self.portfolio_repo.find_by_id(item_id)
        created_item["id"] = str(created_item["_id"])

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Portfolio Item Created",
            entity="Portfolio",
            entity_id=item_id
        )

        logger_portfolio.info(
            f"Portfolio item '{title}' created."
        )

        return created_item

    async def update_portfolio_item(
        self,
        item_id: str,
        current_user: dict,
        **updates
    ) -> dict:
        """Update portfolio item"""

        item = await self.portfolio_repo.find_by_id(item_id)

        if not item:
            raise ResourceNotFoundException("Portfolio Item")

        if "slug" in updates:
            updates["slug"] = updates["slug"].strip().lower()

            existing = await self.portfolio_repo.find_by_slug(
                updates["slug"]
            )

            if existing and str(existing["_id"]) != item_id:
                raise DuplicateException("Slug")

        updated = await self.portfolio_repo.update(
            item_id,
            updates
        )

        if not updated:
            raise ValidationException(
                "Failed to update portfolio item."
            )

        updated = await self.portfolio_repo.find_by_id(item_id)
        updated["id"] = str(updated["_id"])

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Portfolio Item Updated",
            entity="Portfolio",
            entity_id=item_id
        )

        logger_portfolio.info(
            f"Portfolio item {item_id} updated."
        )

        return updated

    async def get_published_items(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get published portfolio items"""

        items = await self.portfolio_repo.find_published(
            skip,
            limit
        )

        for item in items:
            item["id"] = str(item["_id"])

        return items

    async def get_featured_items(
        self,
        limit: int = 10
    ) -> list:
        """Get featured portfolio items"""

        items = await self.portfolio_repo.get_featured(limit)

        for item in items:
            item["id"] = str(item["_id"])

        return items

    async def get_items_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get portfolio items by category"""

        items = await self.portfolio_repo.find_by_category(
            category,
            skip,
            limit
        )

        for item in items:
            item["id"] = str(item["_id"])

        return items

    async def get_portfolio_item(
        self,
        slug: str
    ) -> dict:
        """Get portfolio item by slug"""

        item = await self.portfolio_repo.find_by_slug(
            slug
        )

        if not item:
            raise ResourceNotFoundException(
                "Portfolio Item"
            )

        if not item.get("published"):
            raise ResourceNotFoundException(
                "Portfolio Item"
            )

        item["id"] = str(item["_id"])

        return item

    async def get_all_items(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """Get all portfolio items"""

        items = await self.portfolio_repo.get_all_items(
            skip,
            limit
        )

        for item in items:
            item["id"] = str(item["_id"])

        return items

    async def delete_portfolio_item(
        self,
        item_id: str,
        current_user: dict
    ) -> dict:
        """Delete portfolio item"""

        item = await self.portfolio_repo.find_by_id(
            item_id
        )

        if not item:
            raise ResourceNotFoundException(
                "Portfolio Item"
            )

        deleted = await self.portfolio_repo.delete(
            item_id
        )

        if not deleted:
            raise ValidationException(
                "Failed to delete portfolio item."
            )

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Portfolio Item Deleted",
            entity="Portfolio",
            entity_id=item_id
        )

        logger_portfolio.info(
            f"Portfolio item {item_id} deleted."
        )

        return {
            "message": "Portfolio item deleted successfully."
        }

VALID_WEBSITE_SECTIONS = {
    "hero",
    "about",
    "services",
    "process",
    "technology_stack",
    "portfolio_section",
    "statistics",
    "faq",
    "contact",
    "social",
    "footer",
    "seo"
}

class WebsiteCMSService:
    """Website CMS service"""

    def __init__(self):
        self.website_repo = WebsiteContentRepository()
        self.activity_service = ActivityLogService()

    async def update_section(
        self,
        section: str,
        content: dict,
        current_user: dict
    ) -> dict:
        """Create or update website section"""

        section = section.strip().lower()

        if not section:
            raise ValidationException(
                "Section is required."
            )

        if section not in VALID_WEBSITE_SECTIONS:
            raise ValidationException(
                f"Invalid website section '{section}'."
            )

        if not content:
            raise ValidationException(
                "Content cannot be empty."
            )

        existing = await self.website_repo.find_by_section(
            section
        )

        if existing:

            updated = await self.website_repo.update(
                str(existing["_id"]),
                {
                    "content": content
                }
            )

            if not updated:
                raise ValidationException(
                    "Failed to update website section."
                )

        else:

            section_id = await self.website_repo.create(
                {
                    "section": section,
                    "content": content
                }
            )

            if not section_id:
                raise ValidationException(
                    "Failed to create website section."
                )

        updated_section = await self.website_repo.find_by_section(
            section
        )

        updated_section["id"] = str(updated_section["_id"])

        await self.activity_service.log_activity(
            user_id=current_user["id"],
            user_role=current_user["role"],
            action="Website Content Updated",
            entity="Website",
            entity_id=updated_section["id"]      # ✅ actual document id
        )

        logger_website.info(
            f"Website section updated: {section}"
        )

        return updated_section

    async def get_section(
        self,
        section: str
    ) -> dict:
        """Get website section"""

        section = section.strip().lower()

        if not section:
            raise ValidationException(
                "Section is required."
            )

        content = await self.website_repo.find_by_section(
            section
        )

        if not content:
            raise ResourceNotFoundException(
                "Website Section"
            )

        content["id"] = str(content["_id"])

        return content

    async def get_all_sections(self) -> list:
        """Get all website sections"""

        sections = await self.website_repo.get_all_sections()

        for section in sections:
            section["id"] = str(section["_id"])

        return sections

