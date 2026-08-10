from pydantic import BaseModel, Field

INDUSTRIES = [
    "bakery", "dairy", "meat_poultry", "seafood", "beverages",
    "fruits_vegetables", "grain_milling", "restaurant_food_service",
    "catering", "confectionery", "other",
]


class OnboardingStatus(BaseModel):
    needs_onboarding: bool


class OnboardingSetupRequest(BaseModel):
    industry: str
    process_description: str = Field(min_length=10, max_length=4000)
    plan_name: str | None = None


class OnboardingSetupResponse(BaseModel):
    haccp_plan_id: str
    document_id: str | None = None
    ai_generated: bool
    message: str
