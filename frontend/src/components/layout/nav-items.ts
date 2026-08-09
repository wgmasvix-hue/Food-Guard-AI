import {
  Bot,
  ClipboardCheck,
  FileText,
  FlaskConical,
  LayoutDashboard,
  ListChecks,
  Settings,
  ShieldAlert,
  Thermometer,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/haccp", label: "HACCP", icon: ShieldAlert },
  { href: "/gmp", label: "GMP", icon: ListChecks },
  { href: "/temperature", label: "Temperature Logs", icon: Thermometer },
  { href: "/products", label: "Product Formulation", icon: FlaskConical },
  { href: "/corrective-actions", label: "Corrective Actions", icon: ClipboardCheck },
  { href: "/audits", label: "Audits", icon: ClipboardCheck },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/ai-assistant", label: "AI Assistant", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
];
