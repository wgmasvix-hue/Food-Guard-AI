"""All ORM models — imported here so Base.metadata sees every table."""
from app.models.ai import AIConversation, AIMessage
from app.models.attachment import Attachment
from app.models.audit import Audit, AuditFinding
from app.models.audit_template import AuditAIAnalysis, AuditChecklistItem, AuditTemplate, AuditTemplateItem
from app.models.billing import Subscription, SubscriptionPlan
from app.models.company import Company, Department, Facility, ProductionLine
from app.models.corrective_action import CorrectiveAction
from app.models.document import Document, DocumentVersion
from app.models.employee import Employee
from app.models.enums import (
    AuditChecklistItemResult,
    AuditStatus,
    AuditType,
    CAStatus,
    CCPStatus,
    ChecklistStatus,
    DocumentCategory,
    FormulationStatus,
    GMPCategory,
    HazardType,
    NotificationLevel,
    ProductionLineStatus,
    RiskLevel,
    SignatureMeaning,
    SubscriptionStatus,
    TemperatureUnitType,
    UserRole,
)
from app.models.gmp import Checklist, ChecklistItem, ChecklistTemplate, ChecklistTemplateItem
from app.models.haccp import CCP, HaccpPlan, HaccpReview, Hazard, MonitoringRecord
from app.models.notification import Notification
from app.models.product import Batch, FormulationItem, Ingredient, Product, ProductFormulation
from app.models.signature import DigitalSignature
from app.models.supplier import Supplier
from app.models.system_log import SystemLog
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.models.user import User

__all__ = [
    "AIConversation", "AIMessage", "Attachment", "Audit", "AuditAIAnalysis", "AuditChecklistItem",
    "AuditChecklistItemResult", "AuditFinding", "AuditTemplate", "AuditTemplateItem", "Batch", "CCP",
    "CAStatus", "CCPStatus", "Checklist", "ChecklistItem", "ChecklistStatus", "ChecklistTemplate",
    "ChecklistTemplateItem", "Company", "CorrectiveAction", "Department", "DigitalSignature", "Document",
    "DocumentCategory", "DocumentVersion", "Employee", "Facility", "FormulationItem", "FormulationStatus",
    "GMPCategory",
    "HaccpPlan", "HaccpReview", "Hazard", "HazardType", "Ingredient", "MonitoringRecord",
    "Notification", "NotificationLevel", "Product", "ProductFormulation", "ProductionLine",
    "ProductionLineStatus", "RiskLevel",
    "SignatureMeaning", "Subscription", "SubscriptionPlan", "SubscriptionStatus", "Supplier", "SystemLog",
    "TemperatureLog", "TemperatureUnit", "TemperatureUnitType", "User", "UserRole",
    "AuditStatus", "AuditType",
]
