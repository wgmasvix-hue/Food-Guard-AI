export type UserRole =
  | "super_admin"
  | "company_admin"
  | "qa_manager"
  | "production_supervisor"
  | "food_safety_officer"
  | "auditor"
  | "operator";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  company_id: string | null;
  facility_id: string | null;
  phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  name: string;
  legal_name?: string | null;
  industry?: string | null;
  country?: string | null;
  is_active: boolean;
}

export interface Facility {
  id: string;
  company_id: string;
  name: string;
  facility_type?: string | null;
  address?: string | null;
  manager_name?: string | null;
  is_active: boolean;
}

export interface ProductionLine {
  id: string;
  facility_id: string;
  department_id?: string | null;
  name: string;
  line_type?: string | null;
  capacity_per_hour?: number | null;
  status: "active" | "stopped" | "maintenance";
  notes?: string | null;
  is_active: boolean;
}

export type SignatureMeaning = "audit_completion" | "haccp_plan_approval" | "corrective_action_verification";

export interface DigitalSignature {
  id: string;
  entity_type: string;
  entity_id: string;
  meaning: SignatureMeaning;
  signed_by_id: string;
  typed_name: string;
  ip_address?: string | null;
  signed_at: string;
  notes?: string | null;
}

export interface AuditTemplateItem {
  id: string;
  order: number;
  clause?: string | null;
  question: string;
  guidance?: string | null;
  is_critical: boolean;
}

export interface AuditTemplate {
  id: string;
  company_id?: string | null;
  name: string;
  standard?: string | null;
  description?: string | null;
  is_active: boolean;
  items: AuditTemplateItem[];
}

export interface AuditChecklistItem {
  id: string;
  audit_id: string;
  template_item_id?: string | null;
  clause?: string | null;
  question: string;
  is_critical: boolean;
  result?: string | null;
  comment?: string | null;
  corrective_action_id?: string | null;
}

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface AuditAIAnalysis {
  id: string;
  audit_id: string;
  generated_by_id?: string | null;
  summary: string;
  risk_level: RiskLevel;
  root_cause_analysis?: string | null;
  recommended_corrective_actions?: string | null;
  improvement_plan?: string | null;
  model?: string | null;
  generated_at: string;
}

export interface Attachment {
  id: string;
  entity_type: string;
  entity_id: string;
  uploaded_by_id?: string | null;
  file_path: string;
  file_name?: string | null;
  content_type?: string | null;
  size_bytes?: number | null;
  caption?: string | null;
  created_at: string;
}

export interface HaccpPlan {
  id: string;
  company_id: string;
  facility_id?: string | null;
  product_id?: string | null;
  name: string;
  scope?: string | null;
  process_description?: string | null;
  version: number;
  status: string;
  next_review_date?: string | null;
}

export interface Hazard {
  id: string;
  plan_id: string;
  process_step: string;
  hazard_type: string;
  description: string;
  likelihood: number;
  severity: number;
  control_measures?: string | null;
  is_ccp: boolean;
  justification?: string | null;
  risk_score: number;
}

export interface CCP {
  id: string;
  plan_id: string;
  number: string;
  name: string;
  process_step?: string | null;
  critical_limit_min?: number | null;
  critical_limit_max?: number | null;
  critical_limit_unit?: string | null;
  critical_limit_description?: string | null;
  monitoring_procedure?: string | null;
  monitoring_frequency?: string | null;
  corrective_action_procedure?: string | null;
  verification_procedure?: string | null;
  responsible_role?: string | null;
  status: string;
}

export interface MonitoringRecord {
  id: string;
  ccp_id: string;
  measured_value: number;
  unit?: string | null;
  within_limits: boolean;
  notes?: string | null;
  recorded_at: string;
  corrective_action_id?: string | null;
}

export interface ChecklistTemplateItem {
  id: string;
  order: number;
  question: string;
  guidance?: string | null;
  is_critical: boolean;
}

export interface ChecklistTemplate {
  id: string;
  name: string;
  category: string;
  description?: string | null;
  frequency?: string | null;
  items: ChecklistTemplateItem[];
}

export interface ChecklistItem {
  id: string;
  question: string;
  is_critical: boolean;
  result?: string | null;
  comment?: string | null;
  photo_path?: string | null;
  corrective_action_id?: string | null;
}

export interface Checklist {
  id: string;
  template_id: string;
  facility_id?: string | null;
  inspector_id?: string | null;
  status: string;
  score?: number | null;
  notes?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  items: ChecklistItem[];
}

export interface TemperatureUnit {
  id: string;
  facility_id?: string | null;
  name: string;
  unit_type: string;
  min_temp?: number | null;
  max_temp?: number | null;
  location?: string | null;
  is_active: boolean;
}

export interface TemperatureLog {
  id: string;
  unit_id: string;
  temperature: number;
  within_limits: boolean;
  notes?: string | null;
  recorded_at: string;
  corrective_action_id?: string | null;
}

export interface CorrectiveAction {
  id: string;
  company_id: string;
  facility_id?: string | null;
  title: string;
  issue_description: string;
  source?: string | null;
  root_cause?: string | null;
  corrective_action?: string | null;
  preventive_action?: string | null;
  responsible_id?: string | null;
  deadline?: string | null;
  evidence_photo_path?: string | null;
  verification_notes?: string | null;
  status: string;
  created_at: string;
}

export interface AuditFinding {
  id: string;
  audit_id: string;
  clause?: string | null;
  severity: string;
  description: string;
  evidence?: string | null;
  status: string;
}

export interface Audit {
  id: string;
  title: string;
  audit_type: string;
  standard?: string | null;
  scope?: string | null;
  template_id?: string | null;
  scheduled_date?: string | null;
  completed_date?: string | null;
  status: string;
  score?: number | null;
  summary?: string | null;
  external_auditor?: string | null;
  findings: AuditFinding[];
  checklist_items: AuditChecklistItem[];
}

export interface DocumentVersion {
  id: string;
  version: number;
  file_path?: string | null;
  file_name?: string | null;
  content_type?: string | null;
  size_bytes?: number | null;
  content_text?: string | null;
  change_note?: string | null;
  created_at: string;
}

export interface FGDocument {
  id: string;
  title: string;
  category: string;
  description?: string | null;
  expires_on?: string | null;
  is_archived: boolean;
  versions: DocumentVersion[];
}

export interface DocumentSearchResult {
  document_id: string;
  title: string;
  category: string;
  snippet: string;
}

export interface Notification {
  id: string;
  user_id: string;
  level: "info" | "warning" | "critical";
  title: string;
  message: string;
  link?: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface DashboardSummary {
  compliance_score: number;
  open_corrective_actions: number;
  overdue_corrective_actions: number;
  temperature_alerts_today: number;
  upcoming_audits: Audit[];
  recent_inspections: Checklist[];
  recent_temperature_alerts: TemperatureLog[];
  today_tasks: string[];
  ai_recommendations: string[];
}

export interface AIMessage {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface AIConversation {
  id: string;
  title: string;
  messages: AIMessage[];
}

export interface SubscriptionPlan {
  id: string;
  code: string;
  name: string;
  price_cents: number;
  currency: string;
  billing_interval: string;
  max_facilities: number | null;
  max_employees: number | null;
  ai_assistant_included: boolean;
  ai_credits_per_month: number | null;
  is_self_serve: boolean;
  sort_order: number;
}

export interface Subscription {
  id: string;
  company_id: string;
  plan_id: string;
  status: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  plan: SubscriptionPlan;
  ai_credits_remaining: number | null;
}

export interface EcocashPayment {
  id: string;
  created_at: string;
  company_id: string;
  plan_id: string;
  reference_code: string;
  amount_cents: number;
  currency: string;
  payer_phone: string | null;
  transaction_reference: string | null;
  status: "pending" | "submitted" | "approved" | "rejected";
  submitted_by_id: string | null;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  plan: SubscriptionPlan;
}

export interface Product {
  id: string;
  company_id: string;
  name: string;
  sku?: string | null;
  category?: string | null;
  description?: string | null;
  allergens?: string | null;
  shelf_life_days?: number | null;
  storage_conditions?: string | null;
  intended_use?: string | null;
  is_active: boolean;
}

export interface FormulationItem {
  id: string;
  formulation_id: string;
  supplier_id?: string | null;
  name: string;
  percentage?: number | null;
  quantity?: number | null;
  unit?: string | null;
  unit_cost?: number | null;
  is_allergen: boolean;
  notes?: string | null;
}

export interface ProductFormulation {
  id: string;
  product_id: string;
  version: number;
  status: "draft" | "active" | "archived";
  batch_size?: number | null;
  batch_size_unit?: string | null;
  notes?: string | null;
  created_by_id?: string | null;
  approved_by_id?: string | null;
  approved_at?: string | null;
  items: FormulationItem[];
  total_percentage: number;
  total_cost: number;
  allergens: string[];
}

export interface Supplier {
  id: string;
  company_id: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  approval_status: "pending" | "approved" | "rejected" | "suspended";
  certification?: string | null;
  certification_expires_on?: string | null;
  risk_rating?: "low" | "medium" | "high" | null;
  notes?: string | null;
  is_active: boolean;
}

export interface Batch {
  id: string;
  product_id: string;
  facility_id?: string | null;
  batch_number: string;
  production_date?: string | null;
  expiry_date?: string | null;
  quantity?: number | null;
  unit?: string | null;
  status: "in_production" | "released" | "on_hold" | "recalled";
  recall_reason?: string | null;
}

export interface RawMaterialLot {
  id: string;
  company_id: string;
  supplier_id?: string | null;
  material_name: string;
  lot_number: string;
  received_date?: string | null;
  expiry_date?: string | null;
  quantity_received?: number | null;
  unit?: string | null;
  status: "active" | "quarantined" | "consumed" | "rejected";
  notes?: string | null;
}

export interface BatchLotUsage {
  id: string;
  batch_id: string;
  raw_material_lot_id: string;
  quantity_used?: number | null;
  unit?: string | null;
  raw_material_lot: RawMaterialLot;
}

export interface TraceBatchSummary {
  id: string;
  product_id: string;
  batch_number: string;
  status: string;
  production_date?: string | null;
}

export interface LotTraceResult {
  lot: RawMaterialLot;
  affected_batches: TraceBatchSummary[];
}

export interface BatchTraceResult {
  batch: Batch;
  lots_used: BatchLotUsage[];
}
