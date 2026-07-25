"""Builds the prompt for and parses the response from AI audit analysis."""
import re

from app.models.audit import Audit
from app.models.enums import RiskLevel

SECTION_ORDER = [
    ("summary", "Summary"),
    ("risk_level", "Risk Level"),
    ("root_cause_analysis", "Root Cause Analysis"),
    ("recommended_corrective_actions", "Recommended Corrective Actions"),
    ("improvement_plan", "Improvement Plan"),
]

_RISK_WORDS = {"low": RiskLevel.LOW, "medium": RiskLevel.MEDIUM, "high": RiskLevel.HIGH, "critical": RiskLevel.CRITICAL}


def build_audit_analysis_prompt(audit: Audit) -> str:
    lines = [
        f"Audit: {audit.title}",
        f"Type: {audit.audit_type} | Standard: {audit.standard or 'N/A'} | Status: {audit.status}",
        f"Scope: {audit.scope or 'N/A'}",
        f"Score: {audit.score if audit.score is not None else 'N/A'}",
        f"Auditor summary notes: {audit.summary or '(none provided)'}",
        "",
        f"Findings ({len(audit.findings)}):",
    ]
    if not audit.findings:
        lines.append("- No findings were recorded.")
    for f in audit.findings:
        lines.append(f"- [{f.severity.upper()}] {f.clause or 'General'}: {f.description}")

    checklist_items = [i for i in audit.checklist_items if i.result]
    if checklist_items:
        lines.append("")
        lines.append(f"Checklist results ({len(checklist_items)} answered):")
        for item in checklist_items:
            flag = " (CRITICAL)" if item.is_critical else ""
            lines.append(f"- [{item.result.upper()}]{flag} {item.clause or ''} {item.question}".strip())
            if item.comment:
                lines.append(f"  Comment: {item.comment}")

    return "\n".join(lines)


def parse_audit_analysis(text: str) -> dict:
    """Split the AI's Markdown response into the five expected sections.

    Falls back gracefully: any section not found gets an empty string (or,
    for risk_level, defaults to MEDIUM) rather than raising — a slightly
    malformed AI response shouldn't be a 500 error.
    """
    positions: dict[str, tuple[int, int]] = {}
    for key, heading in SECTION_ORDER:
        match = re.search(rf"^##\s*{re.escape(heading)}\s*$", text, re.MULTILINE | re.IGNORECASE)
        if match:
            positions[key] = (match.start(), match.end())

    ordered = sorted(positions.items(), key=lambda kv: kv[1][0])
    result: dict[str, str] = {}
    for idx, (key, (_, end)) in enumerate(ordered):
        next_start = ordered[idx + 1][1][0] if idx + 1 < len(ordered) else len(text)
        result[key] = text[end:next_start].strip()

    for key, _ in SECTION_ORDER:
        result.setdefault(key, "")

    risk_level = RiskLevel.MEDIUM
    risk_text = result.get("risk_level", "").strip().lower()
    for word, level in _RISK_WORDS.items():
        if risk_text.startswith(word):
            risk_level = level
            break

    return {
        "summary": result["summary"] or text.strip(),
        "risk_level": risk_level,
        "root_cause_analysis": result["root_cause_analysis"],
        "recommended_corrective_actions": result["recommended_corrective_actions"],
        "improvement_plan": result["improvement_plan"],
    }
