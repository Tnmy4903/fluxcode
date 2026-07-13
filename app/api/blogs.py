from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from app.api.auth import get_current_user
from app.db.database import db
from app.db.schemas import BlogCreate, BlogOut

blog_router = APIRouter()


# ───────────────────────────────
# ✍️ Create Blog (Admin Only)
# ───────────────────────────────
@blog_router.post("/", response_model=BlogOut)
async def create_blog(blog: BlogCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    existing_slug = await db.blogs.find_one({"slug": blog.slug})
    if existing_slug:
        raise HTTPException(status_code=400, detail="Slug must be unique")

    new_blog = {
        "title": blog.title,
        "slug": blog.slug,
        "content": blog.content,
        "thumbnail": blog.thumbnail,
        "author": blog.author,
        "views": 0,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = await db.blogs.insert_one(new_blog)
    new_blog["id"] = str(result.inserted_id)
    return BlogOut(**new_blog)


# ───────────────────────────────
# 📄 Get All Blogs (Public)
# ───────────────────────────────
@blog_router.get("/", response_model=List[BlogOut])
async def get_all_blogs():
    blogs_cursor = db.blogs.find().sort("createdAt", -1)
    blogs = []
    async for blog in blogs_cursor:
        blog["id"] = str(blog["_id"])
        blogs.append(BlogOut(**blog))
    return blogs


# ───────────────────────────────
# 📄 Get Blog by Slug + Increment Views
# ───────────────────────────────
@blog_router.get("/{slug}", response_model=BlogOut)
async def get_blog_by_slug(slug: str):
    blog = await db.blogs.find_one({"slug": slug})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    await db.blogs.update_one({"_id": blog["_id"]}, {"$inc": {"views": 1}})
    blog["views"] += 1
    blog["id"] = str(blog["_id"])
    return BlogOut(**blog)


# ───────────────────────────────
# ❌ Delete Blog (Admin Only)
# ───────────────────────────────
@blog_router.delete("/{id}")
async def delete_blog(id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid blog ID")

    result = await db.blogs.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog not found")

    return {"message": "Blog deleted successfully"}
