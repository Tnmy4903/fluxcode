from pydantic import BaseModel, EmailStr
from fastapi import UploadFile
from typing import Optional, List
from datetime import datetime, date

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
    role: str

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
