from pydantic import BaseModel, EmailStr
from fastapi import UploadFile
from typing import Optional, List, Dict, Any
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

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str  # "super_admin" | "sub_admin" | "client"
    phone: Optional[str] = None

# ───────────────────────────────
# 📝 Blog Schemas
# ───────────────────────────────

class BlogCreate(BaseModel):
    title: str
    slug: str
    content: str
    thumbnail: Optional[str] = None
    author: str

class BlogOut(BlogCreate):
    id: str
    views: int
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 📁 Project Schemas
# ───────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: str
    deadline: Optional[date]
    budget: Optional[float]

class ProjectOut(ProjectCreate):
    id: str
    userId: str
    status: str
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 📎 File Upload Schema
# ───────────────────────────────

class FileUploadOut(BaseModel):
    id: str
    userId: str
    projectId: str
    fileName: str
    filePath: str
    uploadedAt: datetime

# ───────────────────────────────
# 🧾 Invoice Schema
# ───────────────────────────────

class InvoiceOut(BaseModel):
    id: str
    projectId: str
    fileUrl: str
    amount: float
    invoiceNumber: str
    isPaid: bool
    currency: str
    generatedOn: datetime

# ───────────────────────────────
# 📬 Contact Form Schemas
# ───────────────────────────────

class ContactFormCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class ContactFormOut(ContactFormCreate):
    id: str
    submittedAt: datetime

# ───────────────────────────────
# 📰 Newsletter Schemas
# ───────────────────────────────

class NewsletterSignup(BaseModel):
    email: EmailStr

class NewsletterOut(BaseModel):
    id: str
    email: EmailStr
    subscribedAt: datetime

class NewsletterBroadcast(BaseModel):
    subject: str
    body: str

class NewsletterSendOut(BaseModel):
    sentTo: int
    subject: str
    status: str

# ───────────────────────────────
# 💼 CRM/Lead Schemas
# ───────────────────────────────

class LeadCreate(BaseModel):
    companyName: str
    contactPerson: str
    phone: str
    email: EmailStr
    business: str
    leadSource: Optional[str] = None
    notes: Optional[str] = None

class LeadUpdate(BaseModel):
    companyName: Optional[str] = None
    contactPerson: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    business: Optional[str] = None
    leadSource: Optional[str] = None
    stage: Optional[str] = None
    assignedTo: Optional[str] = None
    notes: Optional[str] = None

class LeadOut(LeadCreate):
    id: str
    stage: str
    assignedTo: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

class LeadHistoryEvent(BaseModel):
    field: str
    oldValue: Optional[str] = None
    newValue: Optional[str] = None
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
    businessName: str
    businessType: str
    targetAudience: str
    goals: str
    requiredFeatures: List[str]
    preferredTech: List[str]
    referenceWebsites: Optional[List[str]] = None
    logoUrl: Optional[str] = None
    deadline: Optional[date] = None
    budgetRange: Optional[str] = None
    additionalNotes: Optional[str] = None

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
    status: Optional[str] = None
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
    status: str
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
    projectId: str
    title: str
    description: Optional[str] = None

class TimelineEventOut(TimelineEventCreate):
    id: str
    createdBy: str
    timestamp: datetime

# ───────────────────────────────
# 💬 Discussion Schemas
# ───────────────────────────────

class DiscussionMessageCreate(BaseModel):
    projectId: str
    message: str
    attachments: Optional[List[str]] = None

class DiscussionReplyCreate(BaseModel):
    message: str
    attachments: Optional[List[str]] = None

class DiscussionMessageOut(BaseModel):
    id: str
    projectId: str
    authorId: str
    authorName: str
    message: str
    attachments: Optional[List[str]] = None
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
    attachments: Optional[List[str]] = None
    edited: bool = False
    createdAt: datetime
    updatedAt: datetime

# ───────────────────────────────
# 📦 Deliverables Schemas
# ───────────────────────────────

class DeliverablesCreate(BaseModel):
    projectId: str
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
    details: Optional[Dict] = None

class ActivityLogOut(ActivityLogCreate):
    id: str
    timestamp: datetime

# ───────────────────────────────
# 🔔 Notification Schemas
# ───────────────────────────────

class NotificationCreate(BaseModel):
    userId: str
    type: str
    title: str
    message: str
    entityId: Optional[str] = None
    entityType: Optional[str] = None

class NotificationOut(NotificationCreate):
    id: str
    read: bool = False
    createdAt: datetime

# ───────────────────────────────
# 🖼️ Portfolio CMS Schemas
# ───────────────────────────────

class PortfolioItemCreate(BaseModel):
    title: str
    slug: str
    category: str
    description: str
    techStack: List[str]
    websiteUrl: Optional[str] = None
    githubUrl: Optional[str] = None
    images: Optional[List[str]] = None
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

class WebsiteHeroCreate(BaseModel):
    title: str
    subtitle: str
    image: Optional[str] = None
    ctaText: Optional[str] = None
    ctaLink: Optional[str] = None

class WebsiteAboutCreate(BaseModel):
    title: str
    content: str
    image: Optional[str] = None

class WebsiteServiceCreate(BaseModel):
    title: str
    description: str
    icon: Optional[str] = None

class WebsiteFAQCreate(BaseModel):
    question: str
    answer: str
    order: int = 0

class WebsiteContactCreate(BaseModel):
    phone: str
    email: EmailStr
    address: str
    timezone: Optional[str] = None

class WebsiteSocialCreate(BaseModel):
    platform: str
    url: str

class WebsiteContentCreate(BaseModel):
    section: str
    content: Dict

class WebsiteContentOut(BaseModel):
    id: str
    section: str
    content: Dict
    updatedAt: datetime
