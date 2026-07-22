"""
Repository pattern for database access
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone

from app.db.database import db
from app.exceptions import ValidationException
from pymongo import ReturnDocument


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, collection_name: str):
        self.collection = db[collection_name]
        self.collection_name = collection_name
    
    async def find_by_id(self, id: str) -> Optional[Dict]:
        """Find document by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(id)})
            return doc
        except Exception:
            raise ValidationException(
                "Invalid ID format."
            )
    
    async def find_one(self, query: Dict) -> Optional[Dict]:
        """Find single document"""
        return await self.collection.find_one(query)
    
    async def find_many(self, query: Dict = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find multiple documents with pagination"""
        query = query or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def create(self, data: Dict) -> str:
        """Create new document"""
        now = datetime.now(timezone.utc)
        data["createdAt"] = now
        data["updatedAt"] = now
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)
    
    async def update(self, id: str, data: Dict) -> bool:
        """Update document by ID"""

        try:
            data["updatedAt"] = datetime.now(timezone.utc)
            result = await self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
            return result.modified_count > 0
        except Exception:
            raise ValidationException(
                "Invalid ID format."
            )

    async def delete(self, id: str) -> bool:
        """Delete document by ID"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            raise ValidationException(
                "Invalid ID format."
            )
    
    async def count(self, query: Dict = None) -> int:
        """Count documents"""
        query = query or {}
        return await self.collection.count_documents(query)
    
    async def get_next_sequence(self, sequence_name: str) -> int:
        """Get next sequence number using counters collection"""

        result = await db["counters"].find_one_and_update(
            {"_id": sequence_name},
            {
                "$inc": {"sequence": 1},
                "$setOnInsert": {"createdAt": datetime.now(timezone.utc)}
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        return result["sequence"]


class UserRepository(BaseRepository):
    """User-specific repository"""
    
    def __init__(self):
        super().__init__("users")
    
    async def find_by_email(self, email: str) -> Optional[Dict]:
        """Find user by email"""
        return await self.find_one({"email": email})
    
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        user = await self.find_by_email(email)
        return user is not None
    
    async def get_by_role(self, role: str) -> List[Dict]:
        """Get all users by role"""
        return await self.find_many({"role": role})
    
    async def count_by_role(self, role: str) -> int:
        """Count users by role"""
        return await self.count({"role": role})

    async def get_admin_count(self) -> int:
        """Count all admin users"""
        return await self.count({
            "role": {"$in": ["super_admin", "sub_admin"]}
        })


class ProjectRepository(BaseRepository):
    """Project-specific repository"""
    
    def __init__(self):
        super().__init__("projects")
    
    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get user's projects"""
        return await self.find_many(
            {"userId": ObjectId(user_id)},
            skip=skip,
            limit=limit
        )
    
    async def count_by_status(self, status: str) -> int:
        """Count projects by status"""
        return await self.count({"status": status})
    
    async def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all projects sorted by creation date"""
        cursor = self.collection.find().sort("createdAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def count_all(self) -> int:
        """Count all projects"""
        return await self.count({})
    
    async def get_recent_projects(self, limit: int = 5):
        cursor = (
            self.collection.find()
            .sort("createdAt", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]


class InvoiceRepository(BaseRepository):
    """Invoice-specific repository"""
    
    def __init__(self):
        super().__init__("invoices")
    
    async def find_by_project(self, project_id: str) -> Optional[Dict]:
        """Find invoice by project ID"""
        return await self.find_one({"projectId": ObjectId(project_id)})
    
    async def count_paid(self) -> int:
        """Count paid invoices"""
        return await self.count({"isPaid": True})
    
    async def count_unpaid(self) -> int:
        """Count unpaid invoices"""
        return await self.count({"isPaid": False})
    
    async def get_next_invoice_number(self) -> str:
        sequence = await self.get_next_sequence("invoice")
        return f"INV-{sequence:05d}"
    
    async def count_all(self):
        """Count all invoices"""
        return await self.count({})
    
    async def get_recent_invoices(self, limit: int = 5):
        cursor = (
            self.collection.find()
            .sort("generatedOn", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]


class UploadRepository(BaseRepository):
    """Upload-specific repository"""
    
    def __init__(self):
        super().__init__("uploads")
    
    async def find_by_project(self, project_id: str) -> List[Dict]:
        """Find uploads for project"""
        return await self.find_many({"projectId": ObjectId(project_id)})
    
    async def find_by_user(self, user_id: str) -> List[Dict]:
        """Find uploads by user"""
        return await self.find_many({"userId": ObjectId(user_id)})
    
    async def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all uploads sorted by date"""
        cursor = self.collection.find().sort("uploadedAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def find_by_filename(
        self,
        filename: str
    ):
        """Find upload by stored filename"""

        return await self.find_one(
            {
                "storedFileName": filename
            }
        )
    
    async def count_all(self) -> int:
        """Count all uploads"""
        return await self.count({})


class BlogRepository(BaseRepository):
    """Blog-specific repository"""
    
    def __init__(self):
        super().__init__("blogs")
    
    async def find_by_slug(self, slug: str) -> Optional[Dict]:
        """Find blog by slug"""
        return await self.find_one({"slug": slug})
    
    async def slug_exists(self, slug: str) -> bool:
        """Check if slug exists"""
        blog = await self.find_by_slug(slug)
        return blog is not None
    
    async def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all blogs sorted by creation date"""
        cursor = self.collection.find().sort("createdAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def increment_views(self, blog_id: str) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(blog_id)},
            {"$inc": {"views": 1}}
        )
        return result.matched_count > 0


class ContactRepository(BaseRepository):
    """Contact form repository"""
    
    def __init__(self):
        super().__init__("contact_forms")

    async def find_by_email(self, email: str):
        """Find latest contact by email"""
        return await self.find_one({"email": email})
    
    async def count_all(self):
        """Count all contact form submissions"""
        return await self.count({})
    
    async def get_recent_contacts(self, limit: int = 5) -> List[Dict]:
        """Get recent contact form submissions"""
        cursor = (
            self.collection.find()
            .sort("createdAt", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]


class LeadRepository(BaseRepository):
    """Lead/CRM repository"""
    
    def __init__(self):
        super().__init__("leads")
    
    async def find_by_stage(self, stage: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find leads by stage"""
        return await self.find_many({"stage": stage}, skip=skip, limit=limit)
    
    async def find_by_assigned_to(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """Find leads assigned to user"""

        return await self.find_many(
            {"assignedTo": user_id},
            skip=skip,
            limit=limit
        )
    
    async def find_by_email(self, email: str) -> Optional[Dict]:
        """Find lead by email"""
        return await self.find_one({"email": email})
    
    async def count_by_stage(self, stage: str) -> int:
        """Count leads by stage"""
        return await self.count({"stage": stage})
    
    async def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all leads sorted by creation date"""
        cursor = self.collection.find().sort("createdAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def add_history_entry(self, lead_id: str, entry: Dict) -> bool:
        """Add history entry to lead"""
        entry["timestamp"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(lead_id)},
            {"$push": {"history": entry}, "$set": {"updatedAt": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def count_all(self) -> int:
        """Count all leads"""
        return await self.collection.count_documents({})
    
    async def get_recent(
        self,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent leads"""

        cursor = (
            self.collection
            .find()
            .sort("createdAt", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]
    

class RequirementRepository(BaseRepository):
    """Requirements repository"""
    
    def __init__(self):
        super().__init__("requirements")
    
    async def find_by_lead(
        self,
        lead_id: str
    ) -> Optional[Dict]:
        """Find requirements by lead ID"""

        return await self.find_one(
            {
                "leadId": lead_id
            }
        )


    async def find_by_project(
        self,
        project_id: str
    ) -> Optional[Dict]:
        """Find requirements by project ID"""

        return await self.find_one(
            {
                "projectId": project_id
            }
        )


    async def exists_by_lead(
        self,
        lead_id: str
    ) -> bool:
        """Check if requirement exists for lead"""

        return await self.collection.count_documents(
            {
                "leadId": lead_id
            }
        ) > 0


    async def exists_by_project(
        self,
        project_id: str
    ) -> bool:
        """Check if requirement exists for project"""

        return await self.collection.count_documents(
            {
                "projectId": project_id
            }
        ) > 0


class QuotationRepository(BaseRepository):
    """Quotation repository"""
    
    def __init__(self):
        super().__init__("quotations")
    
    async def find_by_client(self, client_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find quotations by client"""
        return await self.find_many({"clientId": client_id}, skip=skip, limit=limit)
    
    async def find_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find quotations by status"""
        return await self.find_many({"status": status}, skip=skip, limit=limit)
    
    async def find_by_project(self, project_id: str) -> Optional[Dict]:
        """Find quotation by project ID"""
        return await self.find_one({"projectId": project_id})
    
    async def get_next_quotation_number(self) -> str:
        """Generate next quotation number"""

        sequence = await self.get_next_sequence(
            "quotation"
        )

        return f"QT-{sequence:05d}"
    
    async def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all quotations sorted by creation date"""
        cursor = self.collection.find().sort("createdAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def find_by_lead(self, lead_id: str) -> Optional[Dict]:
        """Find quotation by lead"""
        return await self.find_one({
            "leadId": lead_id
        })
    
    async def exists_accepted(self, quotation_id: str) -> bool:
        """Check if quotation is already accepted"""

        quotation = await self.find_by_id(quotation_id)

        return (
            quotation is not None
            and quotation.get("status") == "Accepted"
        )

    async def find_by_client_and_id(
        self,
        quotation_id: str,
        client_id: str
    ) -> Optional[Dict]:
        """Find quotation belonging to a client"""

        return await self.find_one(
            {
                "_id": ObjectId(quotation_id),
                "clientId": client_id
            }
        )
    
    async def count_all(self) -> int:
        """Count quotations"""
        return await self.count({})
    
    async def count_by_status(
        self,
        status: str
    ) -> int:
        """Count quotations by status"""

        return await self.count(
            {
                "status": status
            }
        )
    
    async def get_recent(
        self,
        limit: int = 5
    ) -> List[Dict]:
        """Get recent quotations"""

        cursor = (
            self.collection
            .find()
            .sort("createdAt", -1)
            .limit(limit)
        )

        return [
            doc async for doc in cursor
        ]


class TimelineRepository(BaseRepository):
    """Project timeline events repository"""
    
    def __init__(self):
        super().__init__("timeline_events")
    
    async def find_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find timeline events for project"""
        cursor = self.collection.find({"projectId": project_id}).sort("timestamp", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]

    async def get_latest_event(
        self,
        project_id: str
    ):
        """Get latest timeline event"""

        return await self.collection.find_one(
            {
                "projectId": project_id
            },
            sort=[("timestamp", -1)]
        )
    
    async def count_by_project(
        self,
        project_id: str
    ) -> int:
        """Count project timeline events"""

        return await self.collection.count_documents(
            {
                "projectId": project_id
            }
        )


class DiscussionRepository(BaseRepository):
    """Project discussion/messaging repository"""
    
    def __init__(self):
        super().__init__("discussions")
    
    async def find_by_project(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find discussion messages for project"""
        cursor = self.collection.find({"projectId": project_id}).sort("createdAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def add_reply(self, message_id: str, reply: Dict) -> bool:
        """Add reply to message"""
        reply["createdAt"] = datetime.utcnow()
        reply["updatedAt"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$push": {"replies": reply}}
        )
        return result.modified_count > 0
    
    async def mark_seen(self, message_id: str) -> bool:
        """Mark message as seen"""
        result = await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"seen": True}}
        )
        return result.modified_count > 0
    
    async def count_by_project(
        self,
        project_id: str
    ) -> int:
        """Count discussion messages"""

        return await self.collection.count_documents(
            {
                "projectId": project_id
            }
        )
    
    async def get_latest_message(
        self,
        project_id: str
    ):
        """Get latest discussion message"""

        return await self.collection.find_one(
            {
                "projectId": project_id
            },
            sort=[("createdAt", -1)]
        )


class DeliverablesRepository(BaseRepository):
    """Deliverables repository"""
    
    def __init__(self):
        super().__init__("deliverables")
    
    async def find_by_project(self, project_id: str) -> Optional[Dict]:
        """Find deliverables by project ID"""
        return await self.find_one({"projectId": project_id})

    async def exists_by_project(
        self,
        project_id: str
    ) -> bool:
        """Check whether deliverables exist"""

        return await self.collection.count_documents(
            {
                "projectId": project_id
            }
        ) > 0
    
    async def count_all(self) -> int:
        """Count all deliverables"""
        return await self.collection.count_documents({})


class ActivityLogRepository(BaseRepository):
    """Activity log repository"""
    
    def __init__(self):
        super().__init__("activity_logs")
    
    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find activity logs by user"""
        cursor = self.collection.find({"userId": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def find_by_entity(self, entity_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find activity logs by entity"""
        cursor = self.collection.find({"entityId": entity_id}).sort("timestamp", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all activity logs sorted by timestamp"""
        cursor = self.collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def get_recent(self, limit: int = 10):
        cursor = (
            self.collection.find()
            .sort("timestamp", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]


class NotificationRepository(BaseRepository):
    """Notifications repository"""
    
    def __init__(self):
        super().__init__("notifications")
    
    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find notifications for user"""
        cursor = self.collection.find({"userId": user_id}).sort("createdAt", -1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def find_unread_by_user(self, user_id: str) -> List[Dict]:
        """Find unread notifications for user"""
        return await self.find_many({"userId": user_id, "read": False})
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"read": True}}
        )
        return result.modified_count > 0
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for user"""
        result = await self.collection.update_many(
            {"userId": user_id, "read": False},
            {"$set": {"read": True}}
        )
        return result.modified_count
    
    async def delete_many_by_user(
        self,
        user_id: str
    ) -> int:
        """Delete all notifications of a user"""

        result = await self.collection.delete_many(
            {
                "userId": user_id
            }
        )

        return result.deleted_count


class PortfolioRepository(BaseRepository):
    """Portfolio CMS repository"""
    
    def __init__(self):
        super().__init__("portfolio")
    
    async def find_by_slug(self, slug: str) -> Optional[Dict]:
        """Find portfolio item by slug"""
        return await self.find_one({"slug": slug})
    
    async def find_published(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find published portfolio items"""
        cursor = self.collection.find({"published": True}).sort("displayOrder", 1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def find_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Find portfolio items by category"""
        cursor = self.collection.find({"category": category, "published": True}).sort("displayOrder", 1).skip(skip).limit(limit)
        return [doc async for doc in cursor]
    
    async def get_featured(self, limit: int = 10) -> List[Dict]:
        """Get featured portfolio items"""
        cursor = self.collection.find({"featured": True, "published": True}).sort("displayOrder", 1).limit(limit)
        return [doc async for doc in cursor]
    
    async def get_all_items(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """Get all portfolio items"""

        cursor = (
            self.collection
            .find()
            .sort("displayOrder", 1)
            .skip(skip)
            .limit(limit)
        )

        return [doc async for doc in cursor]


class WebsiteContentRepository(BaseRepository):
    """Website CMS content repository"""
    
    def __init__(self):
        super().__init__("website_content")
    
    async def find_by_section(self, section: str) -> Optional[Dict]:
        """Find website content by section"""
        return await self.find_one({"section": section})
    
    async def get_all_sections(self) -> List[Dict]:
        """Get all website sections"""
        return await self.find_many()
