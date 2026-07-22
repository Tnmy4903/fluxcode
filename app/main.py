from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.database import client
from app.config import CORS_ORIGINS

from app.api import (
    auth,
    admin,
    blogs,
    projects,
    invoices,
    uploads,
    contact,
    crm,
    requirements,
    quotations,
    timeline,
    discussions,
    deliverables,
    activity_logs,
    notifications,
    portfolio,
    website_cms
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """

    await client.admin.command("ping")
    print("✅ Connected to MongoDB")

    yield

    client.close()
    print("MongoDB connection closed.")

app = FastAPI(
    title="FluxCode Backend API",
    description="Backend API for FluxCode CRM, Project Management, Portfolio and Website CMS.",
    version="1.0.0",
    lifespan=lifespan
)

# -------------------------------------------------------
# CORS
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------
# Authentication
# -------------------------------------------------------
app.include_router(
    auth.auth_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

# -------------------------------------------------------
# Admin
# -------------------------------------------------------
app.include_router(
    admin.admin_router,
    prefix="/api/admin",
    tags=["Admin"]
)

# -------------------------------------------------------
# Blog
# -------------------------------------------------------
app.include_router(
    blogs.blog_router,
    prefix="/api/blogs",
    tags=["Blogs"]
)

# -------------------------------------------------------
# Projects
# -------------------------------------------------------
app.include_router(
    projects.project_router,
    prefix="/api/projects",
    tags=["Projects"]
)

# -------------------------------------------------------
# Invoices
# -------------------------------------------------------
app.include_router(
    invoices.invoice_router,
    prefix="/api/invoices",
    tags=["Invoices"]
)

# -------------------------------------------------------
# Uploads
# -------------------------------------------------------
app.include_router(
    uploads.upload_router,
    prefix="/api/uploads",
    tags=["Uploads"]
)

# -------------------------------------------------------
# Public APIs
# -------------------------------------------------------
app.include_router(
    contact.contact_router,
    prefix="/api/public",
    tags=["Public"]
)

# -------------------------------------------------------
# CRM
# -------------------------------------------------------
app.include_router(
    crm.lead_router,
    prefix="/api",
    tags=["CRM"]
)

app.include_router(
    requirements.requirement_router,
    prefix="/api",
    tags=["Requirements"]
)

app.include_router(
    quotations.quotation_router,
    prefix="/api",
    tags=["Quotations"]
)

app.include_router(
    timeline.timeline_router,
    prefix="/api",
    tags=["Timeline"]
)

app.include_router(
    discussions.discussion_router,
    prefix="/api",
    tags=["Discussions"]
)

app.include_router(
    deliverables.deliverables_router,
    prefix="/api",
    tags=["Deliverables"]
)

app.include_router(
    activity_logs.activity_router,
    prefix="/api",
    tags=["Activity Logs"]
)

app.include_router(
    notifications.notification_router,
    prefix="/api",
    tags=["Notifications"]
)

# -------------------------------------------------------
# Portfolio & CMS
# -------------------------------------------------------
app.include_router(
    portfolio.portfolio_router,
    prefix="/api",
    tags=["Portfolio"]
)

app.include_router(
    website_cms.website_cms_router,
    prefix="/api",
    tags=["Website CMS"]
)

# -------------------------------------------------------
# Root Endpoint
# -------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {
        "application": "FluxCode Backend API",
        "version": "1.0.0",
        "status": "running"
    }


# -------------------------------------------------------
# Health Check
# -------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health():
    return {
        "application": app.title,
        "version": app.version,
        "status": "healthy"
    }
