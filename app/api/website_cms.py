"""
Website CMS API
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict

from app.services.service_layer import WebsiteCMSService, ActivityLogService
from app.exceptions import exception_to_http
from app.logger import logger_project
from app.api.auth import get_current_user

website_cms_router = APIRouter()
website_service = WebsiteCMSService()
activity_service = ActivityLogService()


@website_cms_router.post("/website/sections/{section}", response_model=dict)
async def update_website_section(section: str, content: Dict, current_user: dict = Depends(get_current_user)):
    """Update website section content (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        valid_sections = ["hero", "about", "services", "process", "technology_stack", 
                         "portfolio_section", "statistics", "faq", "contact", "social", "footer", "seo"]
        
        if section not in valid_sections:
            raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of: {', '.join(valid_sections)}")
        
        result = await website_service.update_section(section, content)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Website Content Updated", "Website", section
        )
        
        logger_project.info(f"Website section updated: {section} by {current_user['email']}")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/sections/{section}", response_model=dict)
async def get_website_section(section: str):
    """Get website section content (Public)"""
    try:
        result = await website_service.get_section(section)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/all", response_model=List[dict])
async def get_all_website_sections():
    """Get all website sections (Public)"""
    try:
        sections = await website_service.get_all_sections()
        return sections
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/hero", response_model=dict)
async def update_hero(hero_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update hero section (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("hero", hero_data)
        
        await activity_service.log_activity(
            current_user["id"], current_user["role"],
            "Hero Section Updated", "Website", "hero"
        )
        
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/hero", response_model=dict)
async def get_hero():
    """Get hero section (Public)"""
    try:
        result = await website_service.get_section("hero")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/about", response_model=dict)
async def update_about(about_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update about section (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("about", about_data)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/about", response_model=dict)
async def get_about():
    """Get about section (Public)"""
    try:
        result = await website_service.get_section("about")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/services", response_model=dict)
async def update_services(services_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update services section (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("services", services_data)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/services", response_model=dict)
async def get_services():
    """Get services section (Public)"""
    try:
        result = await website_service.get_section("services")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/process", response_model=dict)
async def update_process(process_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update development process section (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("process", process_data)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/process", response_model=dict)
async def get_process():
    """Get development process section (Public)"""
    try:
        result = await website_service.get_section("process")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/faq", response_model=dict)
async def update_faq(faq_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update FAQ section (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("faq", faq_data)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/faq", response_model=dict)
async def get_faq():
    """Get FAQ section (Public)"""
    try:
        result = await website_service.get_section("faq")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/contact", response_model=dict)
async def update_contact(contact_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update contact section (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("contact", contact_data)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/contact", response_model=dict)
async def get_contact():
    """Get contact section (Public)"""
    try:
        result = await website_service.get_section("contact")
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.post("/website/social", response_model=dict)
async def update_social(social_data: Dict, current_user: dict = Depends(get_current_user)):
    """Update social links (Super Admin only)"""
    try:
        if current_user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can manage website content")
        
        result = await website_service.update_section("social", social_data)
        return result
    except Exception as e:
        raise exception_to_http(e)


@website_cms_router.get("/website/social", response_model=dict)
async def get_social():
    """Get social links (Public)"""
    try:
        result = await website_service.get_section("social")
        return result
    except Exception as e:
        raise exception_to_http(e)
