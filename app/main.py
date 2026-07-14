from fastapi import FastAPI
from app.db.database import db
from app.api import (
    auth, admin, blogs, projects, uploads, contact, newsletter,
    crm, requirements, quotations, timeline, discussions, deliverables,
    activity_logs, notifications, portfolio, website_cms
)

app = FastAPI()

# Routers
app.include_router(auth.auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin.admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(blogs.blog_router, prefix="/api/blogs", tags=["Blogs"])
app.include_router(projects.project_router, prefix="/api/projects", tags=["Projects"])
app.include_router(uploads.upload_router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(projects.invoice_router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(contact.contact_router, prefix="/api/public", tags=["Public"])
app.include_router(newsletter.newsletter_router, prefix="/api/newsletter", tags=["Newsletter"])

# New CRM & Business Process Routers
app.include_router(crm.lead_router, prefix="/api", tags=["CRM"])
app.include_router(requirements.requirement_router, prefix="/api", tags=["Requirements"])
app.include_router(quotations.quotation_router, prefix="/api", tags=["Quotations"])
app.include_router(timeline.timeline_router, prefix="/api", tags=["Timeline"])
app.include_router(discussions.discussion_router, prefix="/api", tags=["Discussions"])
app.include_router(deliverables.deliverables_router, prefix="/api", tags=["Deliverables"])
app.include_router(activity_logs.activity_router, prefix="/api", tags=["Activity Logs"])
app.include_router(notifications.notification_router, prefix="/api", tags=["Notifications"])
app.include_router(portfolio.portfolio_router, prefix="/api", tags=["Portfolio"])
app.include_router(website_cms.website_cms_router, prefix="/api", tags=["Website CMS"])

@app.get("/")
async def root():
    return {"message": "Backend running successfully"}
