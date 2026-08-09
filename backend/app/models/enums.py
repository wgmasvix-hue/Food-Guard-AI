"""Shared enumerations. Stored as strings for portability and readability."""
from enum import StrEnum


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    COMPANY_ADMIN = "company_admin"
    QA_MANAGER = "qa_manager"
    PRODUCTION_SUPERVISOR = "production_supervisor"
    FOOD_SAFETY_OFFICER = "food_safety_officer"
    AUDITOR = "auditor"
    OPERATOR = "operator"


class HazardType(StrEnum):
    BIOLOGICAL = "biological"
    CHEMICAL = "chemical"
    PHYSICAL = "physical"
    ALLERGEN = "allergen"
    RADIOLOGICAL = "radiological"


class CCPStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"


class GMPCategory(StrEnum):
    PERSONNEL_HYGIENE = "personnel_hygiene"
    CLEANING = "cleaning"
    SANITATION = "sanitation"
    EQUIPMENT = "equipment"
    MAINTENANCE = "maintenance"
    BUILDING_INSPECTION = "building_inspection"
    WATER_QUALITY = "water_quality"
    WASTE_MANAGEMENT = "waste_management"
    PEST_CONTROL = "pest_control"
    CHEMICAL_STORAGE = "chemical_storage"
    VISITOR_CONTROL = "visitor_control"


class ChecklistStatus(StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TemperatureUnitType(StrEnum):
    COLD_ROOM = "cold_room"
    FREEZER = "freezer"
    REFRIGERATOR = "refrigerator"
    COOKING = "cooking"
    COOLING = "cooling"
    HOT_HOLDING = "hot_holding"


class CAStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    CLOSED = "closed"
    OVERDUE = "overdue"


class AuditType(StrEnum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    SUPPLIER = "supplier"
    REGULATORY = "regulatory"


class AuditStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DocumentCategory(StrEnum):
    SOP = "sop"
    POLICY = "policy"
    CERTIFICATE = "certificate"
    SPECIFICATION = "specification"
    SUPPLIER_DOCUMENT = "supplier_document"
    TRAINING_RECORD = "training_record"
    FORM = "form"
    HACCP_PLAN = "haccp_plan"
    OTHER = "other"


class NotificationLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ProductionLineStatus(StrEnum):
    ACTIVE = "active"
    STOPPED = "stopped"
    MAINTENANCE = "maintenance"


class SignatureMeaning(StrEnum):
    """What the signer is attesting to — shown back to them at signing time."""

    AUDIT_COMPLETION = "audit_completion"
    HACCP_PLAN_APPROVAL = "haccp_plan_approval"
    CORRECTIVE_ACTION_VERIFICATION = "corrective_action_verification"


class AuditChecklistItemResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NA = "na"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class FormulationStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class EcocashPaymentStatus(StrEnum):
    PENDING = "pending"  # created, waiting for the customer to pay and submit a reference
    SUBMITTED = "submitted"  # customer submitted a transaction reference, awaiting admin review
    APPROVED = "approved"
    REJECTED = "rejected"
