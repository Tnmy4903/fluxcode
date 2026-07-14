# FluxCode API Quick Reference

## Authentication
All endpoints require JWT token except public endpoints.

## CRM - Leads
```
POST   /api/leads                            - Create lead
GET    /api/leads                            - List leads
GET    /api/leads/{id}                       - Get lead
PUT    /api/leads/{id}                       - Update lead
POST   /api/leads/{id}/assign/{sub_admin_id} - Assign to sub-admin
GET    /api/leads/{id}/history               - View change history
```

## Requirements
```
POST   /api/requirements                          - Create requirement
GET    /api/requirements/{id}                     - Get requirement
PUT    /api/requirements/{id}                     - Update requirement
DELETE /api/requirements/{id}                     - Delete requirement
GET    /api/leads/{lead_id}/requirements          - Get lead requirements
GET    /api/projects/{project_id}/requirements    - Get project requirements
```

## Quotations
```
POST   /api/quotations                     - Create quotation
GET    /api/quotations                     - List quotations
GET    /api/quotations/{id}                - Get quotation
PUT    /api/quotations/{id}                - Update quotation
POST   /api/quotations/{id}/send           - Send quotation
POST   /api/quotations/{id}/accept         - Accept quotation (client)
POST   /api/quotations/{id}/reject         - Reject quotation (client)
POST   /api/quotations/{id}/request-revision - Request revision (client)
DELETE /api/quotations/{id}                - Delete quotation
```

## Project Timeline
```
POST   /api/projects/{project_id}/timeline    - Add timeline event
GET    /api/projects/{project_id}/timeline    - Get timeline
DELETE /api/timeline/{event_id}               - Delete event
```

## Project Discussions
```
POST   /api/projects/{project_id}/discussions       - Add message
GET    /api/projects/{project_id}/discussions       - Get messages
POST   /api/discussions/{message_id}/replies        - Add reply
GET    /api/discussions/{message_id}                - Get message with replies
DELETE /api/discussions/{message_id}                - Delete message
```

## Deliverables
```
POST   /api/projects/{project_id}/deliverables   - Create deliverables
GET    /api/projects/{project_id}/deliverables   - Get deliverables
PUT    /api/projects/{project_id}/deliverables   - Update deliverables
DELETE /api/projects/{project_id}/deliverables   - Delete deliverables
```

## Activity Logs
```
GET /api/activity-logs                   - Get all activity logs
GET /api/activity-logs/user/{user_id}    - Get user activity
GET /api/activity-logs/entity/{entity_id} - Get entity history
GET /api/activity-logs/{id}              - Get specific log
```

## Notifications
```
GET    /api/notifications            - Get notifications
GET    /api/notifications/unread     - Get unread notifications
POST   /api/notifications/{id}/read  - Mark as read
POST   /api/notifications/read-all   - Mark all as read
DELETE /api/notifications/{id}       - Delete notification
POST   /api/notifications/clear-all  - Delete all notifications
```

## Portfolio
```
POST   /api/portfolio                      - Create item (admin)
GET    /api/portfolio/public               - Get published items
GET    /api/portfolio/featured             - Get featured items
GET    /api/portfolio/category/{category}  - Get by category
GET    /api/portfolio/{slug}               - Get item by slug
GET    /api/portfolio-admin/all            - Get all items (admin)
PUT    /api/portfolio-admin/{id}           - Update item (admin)
DELETE /api/portfolio-admin/{id}           - Delete item (admin)
```

## Website CMS
```
POST   /api/website/sections/{section}  - Update section (admin)
GET    /api/website/sections/{section}  - Get section (public)
GET    /api/website/all                 - Get all sections (public)

Specific sections:
POST   /api/website/hero          - Update hero
GET    /api/website/hero          - Get hero
POST   /api/website/about         - Update about
GET    /api/website/about         - Get about
POST   /api/website/services      - Update services
GET    /api/website/services      - Get services
POST   /api/website/process       - Update process
GET    /api/website/process       - Get process
POST   /api/website/faq           - Update FAQ
GET    /api/website/faq           - Get FAQ
POST   /api/website/contact       - Update contact
GET    /api/website/contact       - Get contact
POST   /api/website/social        - Update social
GET    /api/website/social        - Get social
```

## Access Control

| Endpoint | Super Admin | Sub Admin | Client |
|----------|:-----------:|:---------:|:------:|
| Create Lead | ✓ | ✓ | ✗ |
| View Leads | ✓ | ✓ | ✗ |
| Create Quotation | ✓ | ✓ | ✗ |
| Accept Quotation | ✓ | ✓ | ✓ |
| Create Discussion | ✓ | ✓ | ✓ |
| Upload Deliverables | ✓ | ✓ | ✗ |
| View Own Projects | ✓ | ✓ | ✓ |
| Manage Website | ✓ | ✗ | ✗ |
| View Activity Logs | ✓ | ✓ | ✗ |

## Response Format

### Success (2xx)
```json
{
  "id": "60d5ec49c1234567890abc",
  "field1": "value1",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Error (4xx/5xx)
```json
{
  "detail": "Error message description"
}
```

## Pagination Parameters
```
skip: int (default: 0)
limit: int (default: 100, max: 1000)
```

## Filtering Examples
```
GET /api/leads?stage=New
GET /api/leads?stage=Contacted&skip=0&limit=50
GET /api/quotations?status=Draft
GET /api/activity-logs?entity_id=123456
```
