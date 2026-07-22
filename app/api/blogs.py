"""
Blogs API
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user
from app.db.schemas import BlogCreate, BlogOut
from app.exceptions import exception_to_http
from app.services.service_layer import BlogService


blog_router = APIRouter()

blog_service = BlogService()


@blog_router.post(
    "/",
    response_model=BlogOut
)
async def create_blog(
    blog: BlogCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create blog"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can create blogs"
            )

        return await blog_service.create_blog(
            current_user=current_user,
            title=blog.title,
            slug=blog.slug,
            content=blog.content,
            thumbnail=blog.thumbnail,
        )

    except Exception as e:
        raise exception_to_http(e)


@blog_router.get(
    "/",
    response_model=List[BlogOut]
)
async def get_all_blogs():
    """Get all blogs"""

    try:
        return await blog_service.get_all_blogs()

    except Exception as e:
        raise exception_to_http(e)


@blog_router.get(
    "/{slug}",
    response_model=BlogOut
)
async def get_blog_by_slug(
    slug: str
):
    """Get blog by slug"""

    try:
        return await blog_service.get_blog_by_slug(
            slug
        )

    except Exception as e:
        raise exception_to_http(e)


@blog_router.delete(
    "/{blog_id}",
    response_model=dict
)
async def delete_blog(
    blog_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete blog"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only Super Admin can delete blogs"
            )

        return await blog_service.delete_blog(
            blog_id=blog_id,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)