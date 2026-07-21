"""All ORM models — imported here so Base.metadata sees every table."""
from app.models.ai import AIConversation, AIMessage
from app.models.audit import Audit, AuditFinding
from app.models.company import Company, Department, Facility
from app.models.corrective_action import CorrectiveAction
from app.models.document import Document, DocumentVersion
from app.models.employee import Employee
from app.models.enums import (
    AuditStatus,
    AuditType,
    CAStatus,
    CCPStatus,
    ChecklistStatus,
    DocumentCategory,
    GMPCategory,
    HazardType,
    NotificationLevel,
    TemperatureUnitType,
    UserRole,
)
from app.models.gmp import Checklist, ChecklistItem, ChecklistTemplate, ChecklistTemplateItem
from app.models.haccp import CCP, HaccpPlan, HaccpReview, Hazard, MonitoringRecord
from app.models.notification import Notification
from app.models.product import Batch, Ingredient, Product
from app.models.supplier import Supplier
from app.models.system_log import SystemLog
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.models.user import User

__all__ = [
    "AIConversation", "AIMessage", "Audit", "AuditFinding", "Batch", "CCP", "CAStatus",
    "CCPStatus", "Checklist", "ChecklistItem", "ChecklistStatus", "ChecklistTemplate",
    "ChecklistTemplateItem", "Company", "CorrectiveAction", "Department", "Document",
    "DocumentCategory", "DocumentVersion", "Employee", "Facility", "GMPCategory",
    "HaccpPlan", "HaccpReview", "Hazard", "HazardType", "Ingredient", "MonitoringRecord",
    "Notification", "NotificationLevel", "Product", "Supplier", "SystemLog",
    "TemperatureLog", "TemperatureUnit", "TemperatureUnitType", "User", "UserRole",
    "AuditStatus", "AuditType",
]
