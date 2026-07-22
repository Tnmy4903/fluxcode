from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Any, Optional, List, Dict
from datetime import datetime, date
from enum import Enum

# ───────────────────────────────
# 📦 Auth/User Schemas
# ───────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    SUB_ADMIN = "sub_admin"
    CLIENT = "client"


class AdminCreate(BaseModel):
    email: EmailStr
    name: str

class PromoteRequest(BaseModel):
    user_id: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole  # "super_admin" | "sub_admin" | "client"
    phone: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# ───────────────────────────────
# 📝 Blog Schemas
# ───────────────────────────────

class BlogCreate(BaseModel):
    title: str
    slug: str
    content: str
    thumbnail: Optional[HttpUrl]

class BlogOut(BlogCreate):
    id: str
    views: int
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 📁 Project Schemas
# ───────────────────────────────

class ProjectStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DELIVERED = "delivered"
    COMPLETED = "completed"

class ProjectCreate(BaseModel):
    title: str
    description: str
    deadline: Optional[date] = None
    budget: Optional[float] = Field(
        default=None,
        gt=0
    )

class ProjectOut(ProjectCreate):
    id: str
    userId: str

    quotationId: Optional[str] = None
    leadId: Optional[str] = None

    assignedAdmin: Optional[str] = None
    assignedSubAdmin: Optional[str] = None

    status: ProjectStatus

    createdAt: datetime
    updatedAt: datetime

class StatusUpdate(BaseModel):
    status: ProjectStatus


class BudgetUpdate(BaseModel):
    budget: float = Field(gt=0)

# ───────────────────────────────
# 📎 File Upload Schema
# ───────────────────────────────

class FileUploadOut(BaseModel):
    id: str

    userId: str
    projectId: str

    fileName: str
    storedFileName: str
    filePath: str

    fileSize: int
    contentType: Optional[str] = None
    extension: str

    uploadedAt: datetime

# ───────────────────────────────
# 🧾 Invoice Enums
# ───────────────────────────────

class InvoiceStatus(str, Enum):
    GENERATED = "generated"
    SENT = "sent"
    PAID = "paid"
    CANCELLED = "cancelled"


# ───────────────────────────────
# 🧾 Invoice Schemas
# ───────────────────────────────

class InvoiceOut(BaseModel):
    id: str

    # Relationships
    projectId: str
    clientId: str

    # Invoice Details
    invoiceNumber: str
    title: str
    description: Optional[str] = None

    # Financial
    amount: float = Field(gt=0)
    currency: str

    # Payment
    status: InvoiceStatus
    isPaid: bool

    # File
    fileUrl: str

    # Dates
    generatedOn: datetime
    dueDate: Optional[date] = None
    paidOn: Optional[datetime] = None

    createdAt: datetime
    updatedAt: datetime


class PaymentUpdate(BaseModel):
    isPaid: bool

# ───────────────────────────────
# 📬 Contact Form Schemas
# ───────────────────────────────

class ContactFormCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    message: str = Field(
        min_length=10,
        max_length=5000
    )


class ContactFormOut(ContactFormCreate):
    id: str

    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 💼 CRM/Lead Schemas
# ───────────────────────────────

class LeadStage(str, Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    PROPOSAL_SENT = "Proposal Sent"
    NEGOTIATION = "Negotiation"
    WON = "Won"
    LOST = "Lost"

class LeadCreate(BaseModel):
    companyName: Optional[str] = Field(
        default=None,
        max_length=200
    )

    contactPerson: str = Field(
        min_length=2,
        max_length=100
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=20
    )

    business: str = Field(
        min_length=2,
        max_length=150
    )

    notes: Optional[str] = Field(
        default=None,
        max_length=5000
    )

class LeadUpdate(BaseModel):
    companyName: Optional[str] = None
    contactPerson: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    business: Optional[str] = None
    leadSource: Optional[str] = None
    stage: Optional[LeadStage]
    assignedTo: Optional[str] = None
    notes: Optional[str] = None

class LeadOut(LeadCreate):
    id: str
    stage: LeadStage
    assignedTo: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

class LeadHistoryEvent(BaseModel):
    action: str
    field: Optional[str] = None
    oldValue: Optional[str] = None
    newValue: Optional[str] = None
    message: Optional[str] = None
    changedBy: str
    timestamp: datetime

# ───────────────────────────────
# 📋 Requirement Schemas
# ───────────────────────────────

class RequirementStatus(str, Enum):
    PENDING = "PENDING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"

class RequirementCreate(BaseModel):
    leadId: Optional[str] = None
    projectId: Optional[str] = None
    businessName: str = Field(
        min_length=2,
        max_length=200
    )

    businessType: str = Field(
        min_length=2,
        max_length=100
    )

    targetAudience: str = Field(
        min_length=2,
        max_length=300
    )

    goals: str = Field(
        min_length=5,
        max_length=5000
    )

    requiredFeatures: List[str] = Field(
        min_length=1
    )

    preferredTech: List[str] = Field(
        min_length=1
    )

    additionalNotes: Optional[str] = Field(
        default=None,
        max_length=5000
    )

class RequirementUpdate(BaseModel):
    businessName: Optional[str] = None
    businessType: Optional[str] = None
    targetAudience: Optional[str] = None
    goals: Optional[str] = None
    requiredFeatures: Optional[List[str]] = None
    preferredTech: Optional[List[str]] = None
    referenceWebsites: Optional[List[str]] = None
    logoUrl: Optional[str] = None
    deadline: Optional[date] = None
    budgetRange: Optional[str] = None
    additionalNotes: Optional[str] = None

class RequirementOut(RequirementCreate):
    id: str
    status: RequirementStatus
    approvedBy: Optional[str] = None
    approvedAt: Optional[datetime] = None
    remarks: Optional[str] = None
    lastUpdatedBy: Optional[str] = None
    lastUpdatedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

class RequirementApprovalRequest(BaseModel):
    remarks: Optional[str] = None

# ───────────────────────────────
# 💰 Quotation Schemas
# ───────────────────────────────

class QuotationStatus(str, Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    VIEWED = "Viewed"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    REVISION_REQUESTED = "Revision Requested"
    EXPIRED = "Expired"

class QuotationItemCreate(BaseModel):
    description: str
    quantity: float = 1.0
    unitPrice: float
    total: float

class QuotationCreate(BaseModel):
    clientId: str
    leadId: Optional[str] = None
    projectId: Optional[str] = None
    services: List[str]
    items: List[QuotationItemCreate]
    timeline: str
    validity: int
    terms: str
    notes: Optional[str] = None

class QuotationUpdate(BaseModel):
    status: Optional[QuotationStatus] = None
    services: Optional[List[str]] = None
    items: Optional[List[QuotationItemCreate]] = None
    timeline: Optional[str] = None
    validity: Optional[int] = None
    terms: Optional[str] = None
    notes: Optional[str] = None
    revisionCount: Optional[int] = None
    lastRevisedBy: Optional[str] = None
    lastRevisedAt: Optional[datetime] = None

class QuotationOut(QuotationCreate):
    id: str
    quotationNumber: str
    status: QuotationStatus
    totalAmount: float
    createdAt: datetime
    updatedAt: datetime
    revisionCount: int
    lastRevisedBy: Optional[str] = None
    lastRevisedAt: Optional[datetime] = None

# ───────────────────────────────
# 📅 Timeline Event Schemas
# ───────────────────────────────

class TimelineEventCreate(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000
    )

class TimelineEventOut(TimelineEventCreate):
    id: str
    projectId: str
    createdBy: str
    timestamp: datetime

# ───────────────────────────────
# 💬 Discussion Schemas
# ───────────────────────────────

class DiscussionMessageCreate(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000
    )

    attachments: Optional[List[str]] = None

class DiscussionReplyCreate(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000
    )
    attachments: Optional[List[str]] = None

class DiscussionMessageOut(BaseModel):
    id: str
    projectId: str
    authorId: str
    authorName: str
    message: str
    attachments: List[str] = []
    edited: bool = False
    seen: bool = False
    createdAt: datetime
    updatedAt: datetime

class DiscussionReplyOut(BaseModel):
    id: str
    messageId: str
    authorId: str
    authorName: str
    message: str
    attachments: List[str] = []
    edited: bool = False
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 📦 Deliverables Schemas
# ───────────────────────────────

class DeliverablesCreate(BaseModel):
    deploymentUrl: Optional[str] = None
    sourceCode: Optional[str] = None
    documentation: Optional[str] = None
    credentials: Optional[str] = None
    apkUrl: Optional[str] = None
    websiteUrl: Optional[str] = None
    repositoryLink: Optional[str] = None
    notes: Optional[str] = None

class DeliverablesUpdate(BaseModel):
    deploymentUrl: Optional[str] = None
    sourceCode: Optional[str] = None
    documentation: Optional[str] = None
    credentials: Optional[str] = None
    apkUrl: Optional[str] = None
    websiteUrl: Optional[str] = None
    repositoryLink: Optional[str] = None
    notes: Optional[str] = None

class DeliverablesOut(DeliverablesCreate):
    id: str
    projectId: str
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 📊 Activity Log Schemas
# ───────────────────────────────

class ActivityLogCreate(BaseModel):
    userId: str
    userRole: str
    action: str
    entity: str
    entityId: str
    details: Dict[str, Any] = {}

class ActivityLogOut(ActivityLogCreate):
    id: str
    timestamp: datetime

# ───────────────────────────────
# 🔔 Notification Schemas
# ───────────────────────────────

class NotificationOut(BaseModel):
    id: str
    userId: str
    type: str
    title: str
    message: str
    entityId: Optional[str] = None
    entityType: Optional[str] = None
    read: bool = False
    createdAt: datetime

# ───────────────────────────────
# 🖼️ Portfolio CMS Schemas
# ───────────────────────────────

class PortfolioItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)

    slug: str = Field(
        min_length=2,
        max_length=200,
        pattern=r"^[a-z0-9-]+$"
    )

    category: str = Field(
        min_length=2,
        max_length=100
    )

    description: str = Field(
        min_length=10,
        max_length=5000
    )
    techStack: List[str]
    websiteUrl: Optional[str] = None
    githubUrl: Optional[str] = None
    images: List[str] = []
    featured: bool = False
    displayOrder: int = 0

class PortfolioItemUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    techStack: Optional[List[str]] = None
    websiteUrl: Optional[str] = None
    githubUrl: Optional[str] = None
    images: Optional[List[str]] = None
    featured: Optional[bool] = None
    displayOrder: Optional[int] = None
    published: Optional[bool] = None

class PortfolioItemOut(PortfolioItemCreate):
    id: str
    published: bool = True
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 🌐 Website CMS Schemas
# ───────────────────────────────

class WebsiteContentCreate(BaseModel):
    section: str
    content: Dict[str, Any]


class WebsiteContentOut(BaseModel):
    id: str
    section: str
    content: Dict[str, Any]
    updatedAt: datetime