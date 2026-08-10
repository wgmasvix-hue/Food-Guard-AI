import {
  Banknote,
  Bot,
  ClipboardCheck,
  FileText,
  FlaskConical,
  LayoutDashboard,
  ListChecks,
  Settings,
  ShieldAlert,
  Thermometer,
  Truck,
  Waypoints,
  type LucideIcon,
} from "lucide-react";

import type { UserRole } from "@/lib/types";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  roles?: UserRole[]; // omit for "everyone"
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/haccp", label: "HACCP", icon: ShieldAlert },
  { href: "/gmp", label: "GMP", icon: ListChecks },
  { href: "/temperature", label: "Temperature Logs", icon: Thermometer },
  { href: "/products", label: "Product Formulation", icon: FlaskConical },
  { href: "/traceability", label: "Traceability", icon: Waypoints },
  { href: "/suppliers", label: "Suppliers", icon: Truck },
  { href: "/corrective-actions", label: "Corrective Actions", icon: ClipboardCheck },
  { href: "/audits", label: "Audits", icon: ClipboardCheck },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/ai-assistant", label: "AI Assistant", icon: Bot },
  { href: "/admin/ecocash", label: "EcoCash Payments", icon: Banknote, roles: ["super_admin"] },
  { href: "/settings", label: "Settings", icon: Settings },
];
