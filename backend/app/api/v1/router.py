from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    attachments,
    audits,
    auth,
    companies,
    corrective_actions,
    dashboard,
    documents,
    gmp,
    haccp,
    notifications,
    products,
    reports,
    signatures,
    temperature,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(haccp.router, prefix="/haccp", tags=["HACCP"])
api_router.include_router(gmp.router, prefix="/gmp", tags=["GMP"])
api_router.include_router(temperature.router, prefix="/temperature", tags=["Temperature"])
api_router.include_router(corrective_actions.router, prefix="/corrective-actions", tags=["Corrective Actions"])
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(products.router, prefix="/products", tags=["Products & Suppliers"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Assistant"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(signatures.router, prefix="/signatures", tags=["Digital Signatures"])
api_router.include_router(attachments.router, prefix="/attachments", tags=["Attachments"])
