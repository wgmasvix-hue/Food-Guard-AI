"""First-run guided setup: pick an industry, describe the process, and
get a starter HACCP plan (an actual HaccpPlan record, ready to refine
under /haccp) plus an AI-drafted supporting document — instead of a
blank slate. Reuses the same AIProvider/generate flow as the AI
Assistant page; if AI isn't configured, the plan skeleton still gets
created, just without the drafted content.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.core.rbac import require_min_role
from app.models.document import Document, DocumentVersion
from app.models.enums import DocumentCategory, UserRole
from app.models.haccp import HaccpPlan
from app.models.product import Product
from app.models.user import User
from app.schemas.onboarding import (
    INDUSTRIES,
    OnboardingSetupRequest,
    OnboardingSetupResponse,
    OnboardingStatus,
)
from app.services.ai import get_ai_provider
from app.services.ai.prompts import get_document_system_prompt
from app.services.billing.limits import check_ai_credits, consume_ai_credit

router = APIRouter()


@router.get("/status", response_model=OnboardingStatus)
def get_onboarding_status(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Heuristic, not a stored flag: a company "needs onboarding" if it
    has no HACCP plans and no products yet. If everything set up during
    onboarding is later deleted, this will (correctly) suggest it again
    rather than remembering a one-time dismissal — there's genuinely
    nothing set up either way."""
    if not current_user.company_id:
        return OnboardingStatus(needs_onboarding=False)
    has_plan = db.query(HaccpPlan.id).filter(HaccpPlan.company_id == current_user.company_id).first() is not None
    has_product = db.query(Product.id).filter(Product.company_id == current_user.company_id).first() is not None
    return OnboardingStatus(needs_onboarding=not has_plan and not has_product)


@router.get("/industries", response_model=list[str])
def list_industries():
    return INDUSTRIES


@router.post("/setup", response_model=OnboardingSetupResponse)
async def setup(
    payload: OnboardingSetupRequest,
    current_user: User = Depends(require_min_role(UserRole.FOOD_SAFETY_OFFICER)),
    db: Session = Depends(get_db),
):
    industry_label = payload.industry.replace("_", " ")
    plan = HaccpPlan(
        company_id=current_user.company_id,
        name=payload.plan_name or f"{industry_label.title()} HACCP Plan",
        scope=payload.process_description,
        process_description=payload.process_description,
    )
    db.add(plan)
    db.flush()

    document_id = None
    ai_generated = False
    message = "Starter HACCP plan created — refine the hazards and CCPs under HACCP."

    provider = get_ai_provider()
    if await provider.is_available():
        try:
            check_ai_credits(db, current_user.company_id)
            system_prompt = get_document_system_prompt("haccp_plan")
            prompt = (
                f"Industry: {industry_label}. Process description: {payload.process_description}\n\n"
                "Draft a complete starter HACCP plan for this business to review and adapt."
            )
            content = await provider.complete(system_prompt, prompt)
            document = Document(
                company_id=current_user.company_id,
                owner_id=current_user.id,
                title=f"{plan.name} (AI draft)",
                category=DocumentCategory.HACCP_PLAN,
                description="AI-drafted during onboarding — review and adapt to your actual process.",
            )
            db.add(document)
            db.flush()
            document.versions.append(DocumentVersion(uploaded_by_id=current_user.id, version=1, content_text=content))
            consume_ai_credit(db, current_user.company_id)
            document_id = document.id
            ai_generated = True
            message = "Starter HACCP plan created, with an AI-drafted document to guide filling in hazards and CCPs."
        except Exception:
            # AI is best-effort here — the plan skeleton above is the part
            # that matters and is already committed to the session.
            message = "Starter HACCP plan created. The AI draft couldn't be generated right now — you can still ask the AI Assistant for help, or fill in hazards and CCPs directly."

    db.commit()
    db.refresh(plan)
    return OnboardingSetupResponse(
        haccp_plan_id=plan.id, document_id=document_id, ai_generated=ai_generated, message=message
    )
