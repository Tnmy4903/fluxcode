from fastapi import FastAPI
from app.db.database import db
from app.api import auth, admin, blogs, projects, uploads, contact, newsletter

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

@app.get("/")
async def root():
    return {"message": "Backend running successfully"}

