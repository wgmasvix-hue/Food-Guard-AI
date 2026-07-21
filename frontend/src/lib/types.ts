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
  scheduled_date?: string | null;
  completed_date?: string | null;
  status: string;
  score?: number | null;
  summary?: string | null;
  external_auditor?: string | null;
  findings: AuditFinding[];
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

export interface Notification {
  id: string;
  level: string;
  title: string;
  message: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
}
