"""
Portfolio CMS API
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.db.schemas import (
    PortfolioItemCreate,
    PortfolioItemOut,
    PortfolioItemUpdate
)
from app.exceptions import exception_to_http
from app.services.service_layer import PortfolioService


portfolio_router = APIRouter()

portfolio_service = PortfolioService()


@portfolio_router.post(
    "/portfolio",
    response_model=PortfolioItemOut
)
async def create_portfolio_item(
    item: PortfolioItemCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create portfolio item"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can create portfolio items"
            )

        return await portfolio_service.create_portfolio_item(
            current_user=current_user,
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

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get(
    "/portfolio/public",
    response_model=List[PortfolioItemOut]
)
async def get_portfolio_public(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get published portfolio items"""

    try:
        return await portfolio_service.get_published_items(
            skip,
            limit
        )

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get(
    "/portfolio/featured",
    response_model=List[PortfolioItemOut]
)
async def get_featured_portfolio(
    limit: int = Query(10, ge=1, le=100)
):
    """Get featured portfolio items"""

    try:
        return await portfolio_service.get_featured_items(
            limit
        )

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get(
    "/portfolio/category/{category}",
    response_model=List[PortfolioItemOut]
)
async def get_portfolio_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get portfolio items by category"""

    try:
        return await portfolio_service.get_items_by_category(
            category=category,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get(
    "/portfolio/{slug}",
    response_model=PortfolioItemOut
)
async def get_portfolio_item(
    slug: str
):
    """Get portfolio item"""

    try:
        return await portfolio_service.get_portfolio_item(
            slug
        )

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.get(
    "/portfolio-admin/all",
    response_model=List[PortfolioItemOut]
)
async def get_all_portfolio_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get all portfolio items"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can view all portfolio items"
            )

        return await portfolio_service.get_all_items(
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.put(
    "/portfolio-admin/{item_id}",
    response_model=PortfolioItemOut
)
async def update_portfolio_item(
    item_id: str,
    updates: PortfolioItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update portfolio item"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can update portfolio items"
            )

        return await portfolio_service.update_portfolio_item(
            item_id=item_id,
            current_user=current_user,
            **updates.dict(exclude_unset=True)
        )

    except Exception as e:
        raise exception_to_http(e)


@portfolio_router.delete(
    "/portfolio-admin/{item_id}",
    response_model=dict
)
async def delete_portfolio_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete portfolio item"""

    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(
                status_code=403,
                detail="Only super admin can delete portfolio items"
            )

        return await portfolio_service.delete_portfolio_item(
            item_id=item_id,
            current_user=current_user
        )

    except Exception as e:
        raise exception_to_http(e)
