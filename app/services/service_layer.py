"""
Service layer for business logic
"""
from datetime import datetime, date
from uuid import uuid4
from pathlib import Path

from app.repositories import (
    UserRepository, ProjectRepository, InvoiceRepository,
    UploadRepository, BlogRepository, ContactRepository, NewsletterRepository,
    LeadRepository, RequirementRepository, QuotationRepository, TimelineRepository,
    DiscussionRepository, DeliverablesRepository, ActivityLogRepository,
    NotificationRepository, PortfolioRepository, WebsiteContentRepository
)
from app.db.models import hash_password, verify_password
from app.exceptions import (
    AuthenticationException, AuthorizationException, 
    ResourceNotFoundException, DuplicateException, PermissionException, ValidationException
)
from app.logger import logger_auth, logger_project, logger_blog
from app.services.email import send_contact_alert, send_invoice_email, send_mass_email
from app.services.invoice_generator import generate_invoice_pdf


class AuthService:
    """Authentication business logic"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def register_client(self, name: str, email: str, phone: str, password: str) -> dict:
        """Register new client user"""
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
        user = await self.user_repo.find_by_email(email)
        
        if not user or not verify_password(password, user["passwordHash"]):
            logger_auth.warning(f"Login failed: invalid credentials for {email}")
            raise AuthenticationException("Invalid email or password")
        
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    
    async def create_sub_admin(self, email: str, name: str) -> dict:
        """Create new sub-admin (Super Admin only)"""
        if await self.user_repo.email_exists(email):
            raise DuplicateException("Email")
        
        temp_password = f"{email.split('@')[0]}_temp_123"
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
            raise PermissionException("only clients can be promoted")
        
        await self.user_repo.update(user_id, {"role": "sub_admin"})
        logger_auth.info(f"Client promoted to sub-admin: {user['email']}")
        
        user["role"] = "sub_admin"
        user["id"] = str(user["_id"])
        return user


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
            "clientId": quotation["clientId"],
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

        if status not in valid_transitions:
            raise ValidationException("Invalid project status")

        if status not in valid_transitions[current_status]:
            raise ValidationException(
                f"Cannot change project status from "
                f"{current_status} to {status}"
            )    
        
        updated = await self.project_repo.update(project_id, {"status": status})
        
        if updated:
            logger_project.info(f"Project {project_id} status updated to {status}")
        
        return updated
    
    async def set_budget(self, project_id: str, budget: float) -> bool:
        """Set project budget/price"""
        updated = await self.project_repo.update(project_id, {"budget": budget})
        
        if updated:
            logger_project.info(f"Project {project_id} budget set to {budget}")
        
        return updated


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
        project = await self.project_repo.find_by_id(project_id)
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
        if not project:
            raise ResourceNotFoundException("Project")
        
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
            "invoice_number": f"INV-{uuid4().hex[:8].upper()}",
            "deadline": project.get("deadline").strftime("%Y-%m-%d") if project.get("deadline") else "N/A",
            "generated_on": now.strftime("%Y-%m-%d"),
        }
        
        path = Path("app/uploads/invoices")
        pdf_path = generate_invoice_pdf(invoice_data, path)
        
        invoice_db_data = {
            "projectId": project["_id"],
            "fileUrl": str(pdf_path),
            "amount": invoice_data["amount"],
            "invoiceNumber": invoice_data["invoice_number"],
            "isPaid": False,
            "currency": "INR",
            "generatedOn": now
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
                "projectId": project_id
            }
        )

        # Notify Super Admin(s)
        admins = await self.user_repo.get_by_role("super_admin")

        for admin in admins:
            await self.notification_service.create_notification(
                user_id=str(admin["_id"]),
                notif_type="invoice",
                title="Invoice Generated",
                message=f"Invoice generated for project {project['title']}.",
                entity_id=invoice_id,
                entity_type="Invoice"
            )
        
        logger_project.info(f"Invoice generated: {invoice_id} for project {project_id}")
        
        invoice_db_data["id"] = invoice_id
        invoice_db_data["projectId"] = project_id
        return invoice_db_data
    
    async def send_invoice_to_client(self, invoice_id: str) -> dict:
        """Send invoice to client"""
        invoice = await self.invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise ResourceNotFoundException("Invoice")
        
        project = await self.project_repo.find_by_id(str(invoice["projectId"]))
        if not project:
            raise ResourceNotFoundException("Project")
        
        user = await self.user_repo.find_by_id(str(project["userId"]))
        if not user:
            raise ResourceNotFoundException("User")
        
        file_path = invoice["fileUrl"]
        subject = f"📄 Invoice #{invoice['invoiceNumber']} for '{project['title']}'"
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
            raise PermissionException("failed to send email via Mailgun")
        
        logger_project.info(f"Invoice {invoice_id} sent to {user['email']}")
        
        return {"message": "Invoice sent successfully", "email": user["email"]}
    
    async def update_payment_status(self, invoice_id: str, is_paid: bool) -> bool:
        """Update invoice payment status"""

        invoice = await self.invoice_repo.find_by_id(invoice_id)

        if not invoice:
            raise ResourceNotFoundException("Invoice")

        updated = await self.invoice_repo.update(
            invoice_id,
            {
                "isPaid": is_paid
            }
        )

        if updated:

            status_str = "paid" if is_paid else "unpaid"

            logger_project.info(
                f"Invoice {invoice_id} marked as {status_str}"
            )

            # Complete project after successful payment
            if is_paid:

                await self.project_service.update_status(
                    project_id=str(invoice["projectId"]),
                    status="completed"
                )

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

        return updated


class BlogService:
    """Blog business logic"""
    
    def __init__(self):
        self.blog_repo = BlogRepository()
    
    async def create_blog(self, title: str, slug: str, content: str, thumbnail: str, author: str) -> dict:
        """Create new blog"""
        if await self.blog_repo.slug_exists(slug):
            raise DuplicateException("Slug")
        
        blog_data = {
            "title": title,
            "slug": slug,
            "content": content,
            "thumbnail": thumbnail,
            "author": author,
            "views": 0
        }
        
        blog_id = await self.blog_repo.create(blog_data)
        logger_blog.info(f"Blog created: {blog_id} - {slug}")
        
        return {"id": blog_id, **blog_data}
    
    async def get_blog_with_view_count(self, slug: str) -> dict:
        """Get blog and increment view count"""
        blog = await self.blog_repo.find_by_slug(slug)
        
        if not blog:
            raise ResourceNotFoundException("Blog")
        
        # Increment views
        await self.blog_repo.collection.update_one(
            {"_id": blog["_id"]},
            {"$inc": {"views": 1}}
        )
        
        blog["views"] += 1
        blog["id"] = str(blog["_id"])
        
        return blog


class NewsletterService:
    """Newsletter business logic"""
    
    def __init__(self):
        self.newsletter_repo = NewsletterRepository()
    
    async def subscribe(self, email: str) -> dict:
        """Subscribe to newsletter"""
        if await self.newsletter_repo.email_subscribed(email):
            raise DuplicateException("Email already subscribed")
        
        subscriber_id = await self.newsletter_repo.create({"email": email})
        
        return {
            "id": subscriber_id,
            "email": email,
            "subscribedAt": datetime.utcnow()
        }
    
    async def broadcast_newsletter(self, subject: str, body: str, file=None) -> dict:
        """Send newsletter to all subscribers"""
        recipients = await self.newsletter_repo.get_all_subscribers()
        
        if not recipients:
            raise ResourceNotFoundException("No newsletter subscribers")
        
        response = send_mass_email(subject, body, recipients, file)
        
        if response.status_code != 200:
            raise PermissionException("failed to send via Mailgun")
        
        return {
            "sentTo": len(recipients),
            "subject": subject,
            "status": "Sent"
        }


class ContactService:
    """Contact form business logic"""
    
    def __init__(self):
        self.contact_repo = ContactRepository()
        self.lead_repo = LeadRepository()
        self.user_repo = UserRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()

    async def submit_contact_form(self, name: str, email: str, message: str) -> dict:
        """Submit contact form and auto-create CRM lead"""

        # Save contact form
        contact_data = {
            "name": name,
            "email": email,
            "message": message
        }

        contact_id = await self.contact_repo.create(contact_data)

        # Auto create CRM Lead (only if not exists)
        existing_lead = await self.lead_repo.find_by_email(email)

        if existing_lead:

            await self.lead_repo.add_history_entry(
                str(existing_lead["_id"]),
                {
                    "action": "Website Contact Form Submitted Again",
                    "performedBy": "system",
                    "message": message
                }
            )

            await self.activity_service.log_activity(
                user_id="system",
                user_role="system",
                action="Existing Lead Contacted Again",
                entity="Lead",
                entity_id=str(existing_lead["_id"]),
                details={
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

            lead_id = await self.lead_repo.create(lead_data)

            await self.activity_service.log_activity(
                user_id="system",
                user_role="system",
                action="Lead Auto Created",
                entity="Lead",
                entity_id=lead_id,
                details={
                    "source": "Website Contact Form"
                }
            )

            admins = await self.user_repo.get_by_role("super_admin")

            for admin in admins:
                await self.notification_service.create_notification(
                    user_id=str(admin["_id"]),
                    notif_type="lead",
                    title="New Website Lead",
                    message=f"{name} ({email}) submitted a new website enquiry.",
                    entity_id=lead_id,
                    entity_type="Lead"
                )
        # Existing behaviour
        send_contact_alert(name, email, message)

        return {
            "id": contact_id,
            "name": name,
            "email": email,
            "message": message,
            "submittedAt": datetime.utcnow()
        }


class LeadService:
    """Lead/CRM business logic"""
    
    def __init__(self):
        self.lead_repo = LeadRepository()
        self.activity_repo = ActivityLogRepository()
    
    async def create_lead(self, company_name: str, contact_person: str, phone: str, 
                         email: str, business: str, lead_source: str = None, notes: str = None) -> dict:
        """Create new lead from contact form"""
        if await self.lead_repo.find_by_email(email):
            raise DuplicateException("Email already exists as lead")
        
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
        
        lead_id = await self.lead_repo.create(lead_data)
        
        return {
            "id": lead_id,
            "companyName": company_name,
            "contactPerson": contact_person,
            "phone": phone,
            "email": email,
            "business": business,
            "leadSource": lead_data["leadSource"],
            "stage": "New"
        }
    
    async def update_lead(self, lead_id: str, user_id: str, user_role: str, **updates) -> dict:
        """Update lead and track history"""
        lead = await self.lead_repo.find_by_id(lead_id)
        if not lead:
            raise ResourceNotFoundException("Lead")
        
        # Track changes in history
        for field, new_value in updates.items():
            old_value = lead.get(field)
            if old_value != new_value:
                history_entry = {
                    "field": field,
                    "oldValue": str(old_value) if old_value else None,
                    "newValue": str(new_value) if new_value else None,
                    "changedBy": user_id
                }
                await self.lead_repo.add_history_entry(lead_id, history_entry)
        
        await self.lead_repo.update(lead_id, updates)
        updated_lead = await self.lead_repo.find_by_id(lead_id)
        updated_lead["id"] = str(updated_lead["_id"])
        
        return updated_lead
    
    async def assign_lead(self, lead_id: str, sub_admin_id: str) -> dict:
        """Assign lead to sub-admin"""
        lead = await self.lead_repo.find_by_id(lead_id)
        if not lead:
            raise ResourceNotFoundException("Lead")
        
        await self.lead_repo.update(lead_id, {"assignedTo": sub_admin_id})
        
        updated_lead = await self.lead_repo.find_by_id(lead_id)
        updated_lead["id"] = str(updated_lead["_id"])
        
        return updated_lead
    
    async def mark_lead_as_won(
        self,
        lead_id: str,
        user_id: str
    ) -> dict:
        """Mark lead as won after quotation acceptance"""

        lead = await self.lead_repo.find_by_id(lead_id)

        if not lead:
            raise ResourceNotFoundException("Lead")

        # Add history
        await self.lead_repo.add_history_entry(
            lead_id,
            {
                "field": "stage",
                "oldValue": lead.get("stage"),
                "newValue": "Won",
                "changedBy": user_id
            }
        )

        # Update stage
        await self.lead_repo.update(
            lead_id,
            {
                "stage": "Won"
            }
        )

        updated = await self.lead_repo.find_by_id(lead_id)
        updated["id"] = str(updated["_id"])

        return updated

    async def mark_lead_as_lost(
        self,
        lead_id: str,
        user_id: str
    ) -> dict:
        """Mark lead as lost after quotation rejection"""

        lead = await self.lead_repo.find_by_id(lead_id)

        if not lead:
            raise ResourceNotFoundException("Lead")

        await self.lead_repo.add_history_entry(
            lead_id,
            {
                "field": "stage",
                "oldValue": lead.get("stage"),
                "newValue": "Lost",
                "changedBy": user_id
            }
        )

        await self.lead_repo.update(
            lead_id,
            {
                "stage": "Lost"
            }
        )

        updated = await self.lead_repo.find_by_id(lead_id)
        updated["id"] = str(updated["_id"])

        return updated


class RequirementService:
    """Requirements documentation service"""
    
    def __init__(self):
        self.req_repo = RequirementRepository()
        self.lead_repo = LeadRepository()
        self.project_repo = ProjectRepository()
    
    async def create_requirement(
        self,
        lead_id: str = None,
        project_id: str = None,
        created_by: str = None,
        **req_data
    ) -> dict:
        """Create requirement documentation"""

        if not lead_id and not project_id:
            raise PermissionException("Either lead_id or project_id must be provided")
        
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

        req_data["leadId"] = lead_id
        req_data["projectId"] = project_id

        # Business Workflow
        req_data["status"] = "PENDING"
        req_data["approvedBy"] = None
        req_data["approvedAt"] = None
        req_data["remarks"] = None
        req_data["lastUpdatedBy"] = created_by
        req_data["lastUpdatedAt"] = datetime.utcnow()

        req_id = await self.req_repo.create(req_data)

        created_req = await self.req_repo.find_by_id(req_id)
        created_req["id"] = req_id

        return created_req
    
    async def update_requirement(
        self,
        requirement_id: str,
        updated_by: str,
        **updates
    ) -> dict:
        """Update requirement"""

        req = await self.req_repo.find_by_id(requirement_id)

        if not req:
            raise ResourceNotFoundException("Requirement")

        # Approved requirements cannot be edited directly
        if req.get("status") == "APPROVED":
            raise ValidationException(
                "Approved requirement cannot be edited. Request changes first."
            )

        updates["status"] = "PENDING"
        updates["lastUpdatedBy"] = updated_by
        updates["lastUpdatedAt"] = datetime.utcnow()

        await self.req_repo.update(requirement_id, updates)

        updated_req = await self.req_repo.find_by_id(requirement_id)

        updated_req["id"] = str(updated_req["_id"])

        return updated_req
    
    async def approve_requirement(
        self,
        requirement_id: str,
        approved_by: str,
        remarks: str = None
    ) -> dict:

        req = await self.req_repo.find_by_id(requirement_id)

        if not req:
            raise ResourceNotFoundException("Requirement")

        await self.req_repo.update(
            requirement_id,
            {
                "status": "APPROVED",
                "approvedBy": approved_by,
                "approvedAt": datetime.utcnow(),
                "remarks": remarks
            }
        )

        req = await self.req_repo.find_by_id(requirement_id)

        req["id"] = str(req["_id"])

        return req
    
    async def request_changes(
        self,
        requirement_id: str,
        remarks: str
    ) -> dict:

        req = await self.req_repo.find_by_id(requirement_id)

        if not req:
            raise ResourceNotFoundException("Requirement")

        await self.req_repo.update(
            requirement_id,
            {
                "status": "CHANGES_REQUESTED",
                "remarks": remarks
            }
        )

        req = await self.req_repo.find_by_id(requirement_id)

        req["id"] = str(req["_id"])

        return req


class QuotationService:
    """Quotation management service"""
    
    def __init__(self):
        self.lead_repo = LeadRepository()
        self.project_repo = ProjectRepository()
        self.quotation_repo = QuotationRepository()
        self.notification_service = NotificationService()
        self.user_repo = UserRepository()
        self.notification_repo = NotificationRepository()
        self.activity_repo = ActivityLogRepository()
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

        if requirement.get("status") != "APPROVED":
            raise ValidationException(
                "Requirement must be approved before quotation can be created."
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
            "status": "Draft",
            "totalAmount": total_amount
        }
        
        quotation_id = await self.quotation_repo.create(quotation_data)
        quotation_data["id"] = quotation_id
        
        return quotation_data
    
    async def update_quotation_status(self, quotation_id: str, status: str, user_id: str = None) -> dict:
        """Update quotation status"""
        valid_statuses = ["Draft", "Sent", "Viewed", "Accepted", "Rejected", "Revision Requested", "Expired"]
        if status not in valid_statuses:
            raise PermissionException(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        quotation = await self.quotation_repo.find_by_id(quotation_id)
        if not quotation:
            raise ResourceNotFoundException("Quotation")
        
        await self.quotation_repo.update(quotation_id, {"status": status})
        # Business workflow
        if quotation.get("leadId"):

            if status == "Accepted":

                await self.lead_service.mark_lead_as_won(
                    quotation["leadId"],
                    user_id or "system"
                )

            elif status == "Rejected":

                await self.lead_service.mark_lead_as_lost(
                    quotation["leadId"],
                    user_id or "system"
                )
        
        updated = await self.quotation_repo.find_by_id(quotation_id)
        updated["id"] = str(updated["_id"])
        
        return updated
    
    async def send_quotation(self, quotation_id: str) -> dict:
        """Mark quotation as sent"""
        return await self.update_quotation_status(quotation_id, "Sent")
    
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

        if quotation.get("status") == "Accepted":
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

            if requirement.get("status") != "Approved":
                raise PermissionException(
                    "Requirement must be approved before accepting quotation."
                )

        # Update quotation status

        # Update quotation status and trigger business workflow
        quotation = await self.update_quotation_status(
            quotation_id=quotation_id,
            status="Accepted",
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

        return {
            "quotation": quotation,
            "project": project
        }



class TimelineService:
    """Project timeline service"""
    
    def __init__(self):
        self.timeline_repo = TimelineRepository()
        self.activity_repo = ActivityLogRepository()
        self.project_service = ProjectService()
    
    async def add_timeline_event(self, project_id: str, title: str, created_by: str, 
                                 description: str = None) -> dict:
        """Add timeline event"""
        event_data = {
            "projectId": project_id,
            "title": title,
            "description": description,
            "createdBy": created_by
        }
        
        event_id = await self.timeline_repo.create(event_data)
        event_data["id"] = event_id
        event_data["timestamp"] = datetime.utcnow()

        # Synchronize project status from timeline
        title = title.lower()

        status_mapping = {
            "project started": "in_progress",
            "testing started": "testing",
            "deployment started": "deployment",
            "project delivered": "delivered",
            "project completed": "completed"
        }

        if title in status_mapping:
            await self.project_service.update_status(
                project_id,
                status_mapping[title]
            )
        
        return event_data
    
    async def get_project_timeline(self, project_id: str, skip: int = 0, limit: int = 100) -> list:
        """Get timeline for project"""
        events = await self.timeline_repo.find_by_project(project_id, skip, limit)
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


class DiscussionService:
    """Project discussion/messaging service"""
    
    def __init__(self):
        self.discussion_repo = DiscussionRepository()
        self.notification_repo = NotificationRepository()
    
    async def add_message(self, project_id: str, author_id: str, author_name: str,
                         message: str, attachments: list = None) -> dict:
        """Add message to discussion"""
        msg_data = {
            "projectId": project_id,
            "authorId": author_id,
            "authorName": author_name,
            "message": message,
            "attachments": attachments or [],
            "edited": False,
            "seen": False,
            "replies": []
        }
        
        msg_id = await self.discussion_repo.create(msg_data)
        msg_data["id"] = msg_id
        
        return msg_data
    
    async def add_reply(self, message_id: str, author_id: str, author_name: str,
                       message: str, attachments: list = None) -> dict:
        """Add reply to message"""
        reply_data = {
            "messageId": message_id,
            "authorId": author_id,
            "authorName": author_name,
            "message": message,
            "attachments": attachments or [],
            "edited": False
        }
        
        await self.discussion_repo.add_reply(message_id, reply_data)
        reply_data["id"] = str(uuid4())
        
        return reply_data
    
    async def get_project_discussion(self, project_id: str, skip: int = 0, limit: int = 100) -> list:
        """Get all messages for project"""
        messages = await self.discussion_repo.find_by_project(project_id, skip, limit)
        for msg in messages:
            msg["id"] = str(msg["_id"])
        return messages
    
    async def initialize_project_discussion(
        self,
        project_id: str,
        created_by: str = "system"
    ):
        """Initialize discussion thread for new project"""

        await self.add_message(
            project_id=project_id,
            author_id=created_by,
            author_name="System",
            message="Project discussion has been initialized. All future communication regarding this project will happen here."
        )


class DeliverablesService:
    """Deliverables management service"""
    
    def __init__(self):
        self.deliverables_repo = DeliverablesRepository()
        self.project_repo = ProjectRepository()
        self.activity_service = ActivityLogService()
        self.notification_service = NotificationService()
        self.user_repo = UserRepository()
    
    async def create_deliverables(self, project_id: str, **deliverables_data) -> dict:
        """Create deliverables for project"""
        project = await self.project_repo.find_by_id(project_id)

        if not project:
            raise ResourceNotFoundException("Project")

        # Project must be active
        if project.get("status") not in ["in_progress", "testing", "deployment"]:
            raise ValidationException(
                "Deliverables can only be created for active projects."
            )

        # Prevent duplicate deliverables
        existing = await self.deliverables_repo.find_by_project(project_id)

        if existing:
            raise ValidationException(
                "Deliverables already exist for this project."
            )
        
        deliverables_data["projectId"] = project_id
        
        del_id = await self.deliverables_repo.create(deliverables_data)
        deliverables_data["id"] = del_id

        await self.activity_service.log_activity(
            user_id="system",
            user_role="system",
            action="Deliverables Created",
            entity="Deliverables",
            entity_id=del_id,
            details={
                "projectId": project_id
            }
        )

        # Notify Super Admin(s)
        admins = await self.user_repo.get_by_role("super_admin")

        for admin in admins:
            await self.notification_service.create_notification(
                user_id=str(admin["_id"]),
                notif_type="deliverables",
                title="Deliverables Created",
                message=f"Deliverables created for project {project_id}.",
                entity_id=del_id,
                entity_type="Deliverables"
            )
        
        return deliverables_data
    
    async def update_deliverables(self, project_id: str, **updates) -> dict:
        """Update deliverables"""
        deliverable = await self.deliverables_repo.find_by_project(project_id)
        if not deliverable:
            raise ResourceNotFoundException("Deliverables")
        
        await self.deliverables_repo.update(str(deliverable["_id"]), updates)
        
        updated = await self.deliverables_repo.find_by_project(project_id)
        updated["id"] = str(updated["_id"])
        
        return updated


class ActivityLogService:
    """Activity logging service"""
    
    def __init__(self):
        self.activity_repo = ActivityLogRepository()
    
    async def log_activity(self, user_id: str, user_role: str, action: str,
                          entity: str, entity_id: str, details: dict = None) -> dict:
        """Log user activity"""
        log_data = {
            "userId": user_id,
            "userRole": user_role,
            "action": action,
            "entity": entity,
            "entityId": entity_id,
            "details": details or {}
        }
        
        log_id = await self.activity_repo.create(log_data)
        log_data["id"] = log_id
        log_data["timestamp"] = datetime.utcnow()
        
        return log_data
    
    async def get_entity_history(self, entity_id: str, skip: int = 0, limit: int = 100) -> list:
        """Get activity history for entity"""
        logs = await self.activity_repo.find_by_entity(entity_id, skip, limit)
        for log in logs:
            log["id"] = str(log["_id"])
        return logs


class NotificationService:
    """Notification management service"""
    
    def __init__(self):
        self.notification_repo = NotificationRepository()
    
    async def create_notification(self, user_id: str, notif_type: str, title: str, message: str,
                                 entity_id: str = None, entity_type: str = None) -> dict:
        """Create notification for user"""
        notif_data = {
            "userId": user_id,
            "type": notif_type,
            "title": title,
            "message": message,
            "entityId": entity_id,
            "entityType": entity_type,
            "read": False
        }
        
        notif_id = await self.notification_repo.create(notif_data)
        notif_data["id"] = notif_id
        
        return notif_data
    
    async def get_user_notifications(self, user_id: str, skip: int = 0, limit: int = 100) -> list:
        """Get notifications for user"""
        notifications = await self.notification_repo.find_by_user(user_id, skip, limit)
        for notif in notifications:
            notif["id"] = str(notif["_id"])
        return notifications
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        return await self.notification_repo.mark_as_read(notification_id)
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read"""
        return await self.notification_repo.mark_all_as_read(user_id)


class PortfolioService:
    """Portfolio CMS service"""
    
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
    
    async def create_portfolio_item(self, title: str, slug: str, category: str, description: str,
                                   tech_stack: list, website_url: str = None, github_url: str = None,
                                   images: list = None, featured: bool = False, 
                                   display_order: int = 0, published: bool = True) -> dict:
        """Create portfolio item"""
        if await self.portfolio_repo.find_by_slug(slug):
            raise DuplicateException("Slug already exists")
        
        item_data = {
            "title": title,
            "slug": slug,
            "category": category,
            "description": description,
            "techStack": tech_stack,
            "websiteUrl": website_url,
            "githubUrl": github_url,
            "images": images or [],
            "featured": featured,
            "displayOrder": display_order,
            "published": published
        }
        
        item_id = await self.portfolio_repo.create(item_data)
        item_data["id"] = item_id
        
        return item_data
    
    async def update_portfolio_item(self, item_id: str, **updates) -> dict:
        """Update portfolio item"""
        item = await self.portfolio_repo.find_by_id(item_id)
        if not item:
            raise ResourceNotFoundException("Portfolio Item")
        
        await self.portfolio_repo.update(item_id, updates)
        
        updated = await self.portfolio_repo.find_by_id(item_id)
        updated["id"] = str(updated["_id"])
        
        return updated
    
    async def get_published_items(self, skip: int = 0, limit: int = 100) -> list:
        """Get published portfolio items"""
        items = await self.portfolio_repo.find_published(skip, limit)
        for item in items:
            item["id"] = str(item["_id"])
        return items
    
    async def get_featured_items(self, limit: int = 10) -> list:
        """Get featured portfolio items"""
        items = await self.portfolio_repo.get_featured(limit)
        for item in items:
            item["id"] = str(item["_id"])
        return items


class WebsiteCMSService:
    """Website CMS service"""
    
    def __init__(self):
        self.website_repo = WebsiteContentRepository()
    
    async def update_section(self, section: str, content: dict) -> dict:
        """Update website section content"""
        existing = await self.website_repo.find_by_section(section)
        
        if existing:
            await self.website_repo.update(str(existing["_id"]), {"content": content})
            updated = await self.website_repo.find_by_section(section)
        else:
            section_data = {
                "section": section,
                "content": content
            }
            section_id = await self.website_repo.create(section_data)
            updated = await self.website_repo.find_by_id(section_id)
        
        updated["id"] = str(updated["_id"])
        return updated
    
    async def get_section(self, section: str) -> dict:
        """Get website section content"""
        content = await self.website_repo.find_by_section(section)
        if not content:
            raise ResourceNotFoundException("Website Section")
        
        content["id"] = str(content["_id"])
        return content
    
    async def get_all_sections(self) -> list:
        """Get all website sections"""
        sections = await self.website_repo.get_all_sections()
        for section in sections:
            section["id"] = str(section["_id"])
        return sections
