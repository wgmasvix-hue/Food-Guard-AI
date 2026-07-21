"""Seed the database with a demo company, users, and sample HACCP/GMP/temperature data.

Run with: python -m app.db.seed
"""
from datetime import date, datetime, timedelta, timezone

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.audit import Audit
from app.models.company import Company, Department, Facility
from app.models.corrective_action import CorrectiveAction
from app.models.enums import (
    AuditStatus,
    AuditType,
    CAStatus,
    ChecklistStatus,
    GMPCategory,
    HazardType,
    TemperatureUnitType,
    UserRole,
)
from app.models.gmp import Checklist, ChecklistItem, ChecklistTemplate, ChecklistTemplateItem
from app.models.haccp import CCP, HaccpPlan, Hazard, MonitoringRecord
from app.models.product import Product
from app.models.temperature import TemperatureLog, TemperatureUnit
from app.models.user import User

DEMO_PASSWORD = "FoodGuard!234"


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Company).filter(Company.name == "Demo Foods Inc.").first():
            print("Seed data already present — skipping.")
            return

        company = Company(
            name="Demo Foods Inc.",
            legal_name="Demo Foods Incorporated",
            industry="Dairy & Bakery Manufacturing",
            country="United States",
            email="ops@demo.foodguard.ai",
        )
        db.add(company)
        db.flush()

        facility = Facility(
            company_id=company.id, name="Main Production Plant", facility_type="plant",
            address="100 Industrial Way, Springfield", manager_name="Alex Rivera",
        )
        db.add(facility)
        db.flush()

        production_dept = Department(facility_id=facility.id, name="Production")
        qa_dept = Department(facility_id=facility.id, name="Quality Assurance")
        db.add_all([production_dept, qa_dept])

        users = [
            User(email="admin@demo.foodguard.ai", full_name="Alex Rivera", role=UserRole.COMPANY_ADMIN,
                 company_id=company.id, facility_id=facility.id, hashed_password=hash_password(DEMO_PASSWORD)),
            User(email="qa.manager@demo.foodguard.ai", full_name="Jordan Lee", role=UserRole.QA_MANAGER,
                 company_id=company.id, facility_id=facility.id, hashed_password=hash_password(DEMO_PASSWORD)),
            User(email="fso@demo.foodguard.ai", full_name="Sam Patel", role=UserRole.FOOD_SAFETY_OFFICER,
                 company_id=company.id, facility_id=facility.id, hashed_password=hash_password(DEMO_PASSWORD)),
            User(email="supervisor@demo.foodguard.ai", full_name="Casey Morgan", role=UserRole.PRODUCTION_SUPERVISOR,
                 company_id=company.id, facility_id=facility.id, hashed_password=hash_password(DEMO_PASSWORD)),
            User(email="auditor@demo.foodguard.ai", full_name="Riley Chen", role=UserRole.AUDITOR,
                 company_id=company.id, facility_id=facility.id, hashed_password=hash_password(DEMO_PASSWORD)),
            User(email="operator@demo.foodguard.ai", full_name="Taylor Nguyen", role=UserRole.OPERATOR,
                 company_id=company.id, facility_id=facility.id, hashed_password=hash_password(DEMO_PASSWORD)),
            User(email="superadmin@foodguard.ai", full_name="Platform Admin", role=UserRole.SUPER_ADMIN,
                 hashed_password=hash_password(DEMO_PASSWORD)),
        ]
        db.add_all(users)
        db.flush()
        qa_manager = users[1]
        fso = users[2]
        supervisor = users[3]
        auditor = users[4]
        operator = users[5]

        product = Product(
            company_id=company.id, name="Peanut Butter Cookies", sku="PBC-500",
            category="Bakery", allergens="peanuts, tree nuts, wheat, milk",
            shelf_life_days=180, storage_conditions="Store in a cool, dry place (< 25°C)",
        )
        db.add(product)
        db.flush()

        # --- HACCP plan ---
        plan = HaccpPlan(
            company_id=company.id, facility_id=facility.id, product_id=product.id,
            name="Peanut Butter Cookies HACCP Plan", version=1, status="approved",
            approved_by_id=qa_manager.id, approved_at=datetime.now(timezone.utc),
            next_review_date=date.today() + timedelta(days=180),
            process_description="Mixing -> Baking -> Cooling -> Metal Detection -> Packaging",
        )
        db.add(plan)
        db.flush()

        baking_hazard = Hazard(
            plan_id=plan.id, process_step="Baking", hazard_type=HazardType.BIOLOGICAL,
            description="Survival of pathogens (Salmonella) due to insufficient bake time/temperature",
            likelihood=2, severity=5, control_measures="Validated time/temperature bake profile",
            is_ccp=True, justification="No subsequent kill step; Q2 of CCP decision tree = Yes",
        )
        metal_hazard = Hazard(
            plan_id=plan.id, process_step="Metal Detection", hazard_type=HazardType.PHYSICAL,
            description="Metal fragment contamination from processing equipment",
            likelihood=2, severity=4, control_measures="In-line metal detector with reject mechanism",
            is_ccp=True, justification="Metal detector is the only control point before packaging",
        )
        db.add_all([baking_hazard, metal_hazard])
        db.flush()

        ccp_bake = CCP(
            plan_id=plan.id, hazard_id=baking_hazard.id, number="CCP-1", name="Oven Baking",
            process_step="Baking", critical_limit_min=190, critical_limit_max=210,
            critical_limit_unit="°C", critical_limit_description="Core temperature 190-210°C for >= 12 minutes",
            monitoring_procedure="Continuous oven temperature logging via calibrated probe",
            monitoring_frequency="Continuous, reviewed every batch",
            corrective_action_procedure="Hold batch, re-bake or reject if below minimum core temperature",
            verification_procedure="Daily calibration check of oven probes",
            responsible_role="production_supervisor",
        )
        ccp_metal = CCP(
            plan_id=plan.id, hazard_id=metal_hazard.id, number="CCP-2", name="Metal Detection",
            process_step="Metal Detection", critical_limit_description="No detectable Fe 2.0mm / Non-Fe 2.5mm / SS 3.0mm",
            monitoring_procedure="Test with certified test pieces at start/end of run and every 2 hours",
            monitoring_frequency="Every 2 hours",
            corrective_action_procedure="Stop line, isolate product since last successful test, re-test detector",
            verification_procedure="Weekly detector sensitivity audit",
            responsible_role="food_safety_officer",
        )
        db.add_all([ccp_bake, ccp_metal])
        db.flush()

        db.add(MonitoringRecord(
            ccp_id=ccp_bake.id, recorded_by_id=supervisor.id, measured_value=198, unit="°C",
            within_limits=True, recorded_at=datetime.now(timezone.utc) - timedelta(hours=3),
        ))
        db.add(MonitoringRecord(
            ccp_id=ccp_metal.id, recorded_by_id=fso.id, measured_value=1, unit="pass",
            within_limits=True, recorded_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ))

        # --- GMP checklist template + a completed inspection ---
        template = ChecklistTemplate(
            company_id=company.id, name="Daily Personnel Hygiene Check", category=GMPCategory.PERSONNEL_HYGIENE,
            frequency="daily",
            items=[
                ChecklistTemplateItem(order=1, question="Hair fully covered / hairnet worn", is_critical=True),
                ChecklistTemplateItem(order=2, question="Hands washed and sanitized before shift", is_critical=True),
                ChecklistTemplateItem(order=3, question="No jewelry worn on hands/wrists", is_critical=False),
                ChecklistTemplateItem(order=4, question="Clean uniform / PPE worn", is_critical=False),
            ],
        )
        db.add(template)
        db.flush()

        checklist = Checklist(
            template_id=template.id, company_id=company.id, facility_id=facility.id,
            inspector_id=fso.id, status=ChecklistStatus.COMPLETED, score=100.0,
            started_at=datetime.now(timezone.utc) - timedelta(hours=2),
            completed_at=datetime.now(timezone.utc) - timedelta(hours=1, minutes=45),
        )
        checklist.items = [
            ChecklistItem(question=i.question, is_critical=i.is_critical, result="pass", template_item_id=i.id)
            for i in template.items
        ]
        db.add(checklist)

        # --- Temperature units + logs (one alert) ---
        cold_room = TemperatureUnit(
            company_id=company.id, facility_id=facility.id, name="Cold Room 1",
            unit_type=TemperatureUnitType.COLD_ROOM, min_temp=0, max_temp=4, location="Warehouse A",
        )
        freezer = TemperatureUnit(
            company_id=company.id, facility_id=facility.id, name="Freezer 1",
            unit_type=TemperatureUnitType.FREEZER, min_temp=-25, max_temp=-18, location="Warehouse A",
        )
        db.add_all([cold_room, freezer])
        db.flush()

        db.add(TemperatureLog(
            unit_id=cold_room.id, recorded_by_id=operator.id, temperature=3.2, within_limits=True,
            recorded_at=datetime.now(timezone.utc) - timedelta(hours=4),
        ))
        alert_ca = CorrectiveAction(
            company_id=company.id, facility_id=facility.id, raised_by_id=operator.id,
            title="Temperature alert: Freezer 1",
            issue_description="Recorded -14.0°C outside limits (-25°C - -18°C) for Freezer 1.",
            source="temperature", status=CAStatus.OPEN, deadline=date.today() + timedelta(days=2),
        )
        db.add(alert_ca)
        db.flush()
        db.add(TemperatureLog(
            unit_id=freezer.id, recorded_by_id=operator.id, temperature=-14.0, within_limits=False,
            recorded_at=datetime.now(timezone.utc) - timedelta(hours=1),
            corrective_action_id=alert_ca.id,
        ))

        # --- Audit ---
        audit = Audit(
            company_id=company.id, facility_id=facility.id, lead_auditor_id=auditor.id,
            title="Q3 Internal HACCP & GMP Audit", audit_type=AuditType.INTERNAL, standard="ISO 22000",
            scope="Full production facility", scheduled_date=date.today() + timedelta(days=14),
            status=AuditStatus.SCHEDULED,
        )
        db.add(audit)

        db.commit()
        print("Seed data created.")
        print(f"  Company admin login: admin@demo.foodguard.ai / {DEMO_PASSWORD}")
        print(f"  Super admin login:   superadmin@foodguard.ai / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
