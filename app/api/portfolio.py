"""
Portfolio CMS API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from app.db.schemas import PortfolioItemCreate, PortfolioItemUpdate
from app.services.service_layer import PortfolioService, ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

portfolio_router = APIRouter()
portfolio_service = PortfolioService()
activity_service = ActivityLogService()


@portfolio_router.post("/portfolio", response_model=dict)
async def create_portfolio_item(item: PortfolioItemCreate, current_user: dict = Depends(get_current_user)):
    """Create portfolio item (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can create portfolio items")
        
        result = await portfolio_service.create_portfolio_item(
            title=item.title,
            slug=item.slug,
            category=item.category,
            description=item.description,
            tech_stack=item.techStack,
            website_url=item.websiteUrl,
            github_url=item.githubUrl,
            images=item.images,
            featured=item.featured,
            display_order=item.displayOrder,
            published=True
        )
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Portfolio Item Created", "Portfolio", result["id"]
        )
        
        logger_project.info(f"Portfolio item created: {result['slug']} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get("/portfolio/public", response_model=List[dict])
async def get_portfolio_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get published portfolio items (Public)"""
    try:
        items = await portfolio_service.get_published_items(skip, limit)
        return items
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get("/portfolio/featured", response_model=List[dict])
async def get_featured_portfolio(limit: int = Query(10, ge=1, le=100)):
    """Get featured portfolio items (Public)"""
    try:
        items = await portfolio_service.get_featured_items(limit)
        return items
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get("/portfolio/category/{category}", response_model=List[dict])
async def get_portfolio_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get portfolio items by category (Public)"""
    try:
        items = await portfolio_service.portfolio_repo.find_by_category(category, skip, limit)
        
        for item in items:
            item["id"] = str(item["_id"])
        
        return items
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get("/portfolio/{slug}", response_model=dict)
async def get_portfolio_item(slug: str):
    """Get portfolio item by slug (Public)"""
    try:
        item = await portfolio_service.portfolio_repo.find_by_slug(slug)
        if not item:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        
        if not item.get("published"):
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        
        item["id"] = str(item["_id"])
        return item
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get("/portfolio-admin/all", response_model=List[dict])
async def get_all_portfolio_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get all portfolio items including drafts (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can view all portfolio items")
        
        items = await portfolio_service.portfolio_repo.find_many({}, skip, limit)
        
        for item in items:
            item["id"] = str(item["_id"])
        
        return items
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.put("/portfolio-admin/{item_id}", response_model=dict)
async def update_portfolio_item(item_id: str, updates: PortfolioItemUpdate, current_user: dict = Depends(get_current_user)):
    """Update portfolio item (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can update portfolio items")
        
        update_dict = updates.dict(exclude_unset=True)
        result = await portfolio_service.update_portfolio_item(item_id, **update_dict)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Portfolio Item Updated", "Portfolio", item_id
        )
        
        logger_project.info(f"Portfolio item updated: {item_id}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.delete("/portfolio-admin/{item_id}", response_model=dict)
async def delete_portfolio_item(item_id: str, current_user: dict = Depends(get_current_user)):
    """Delete portfolio item (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can delete portfolio items")
        
        item = await portfolio_service.portfolio_repo.find_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        
        deleted = await portfolio_service.portfolio_repo.delete(item_id)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Portfolio Item Deleted", "Portfolio", item_id
        )
        
        return {"message": "Portfolio item deleted successfully"}
    except Exception as e:
        raise exception_to_http(e)
