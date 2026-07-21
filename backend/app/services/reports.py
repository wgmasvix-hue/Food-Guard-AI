"""PDF report generation using ReportLab.

Each function returns raw PDF bytes so API endpoints can stream them
directly as a download without touching the filesystem.
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BRAND_GREEN = colors.HexColor("#16a34a")
DARK_GRAY = colors.HexColor("#1f2937")

styles = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("FGTitle", parent=styles["Title"], textColor=BRAND_GREEN)
SUBTITLE_STYLE = ParagraphStyle("FGSubtitle", parent=styles["Normal"], textColor=DARK_GRAY, fontSize=10)
H2_STYLE = ParagraphStyle("FGH2", parent=styles["Heading2"], textColor=DARK_GRAY, spaceBefore=12)


def _build_pdf(title: str, subtitle: str, elements: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    story = [
        Paragraph("Food Guard AI", TITLE_STYLE),
        Paragraph(title, SUBTITLE_STYLE),
        Paragraph(subtitle, SUBTITLE_STYLE),
        Spacer(1, 0.6 * cm),
        *elements,
    ]
    doc.build(story)
    return buffer.getvalue()


def _table(headers: list[str], rows: list[list[str]]) -> Table:
    data = [headers] + rows if rows else [headers, ["No records found"] + [""] * (len(headers) - 1)]
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _generated_line(company_name: str) -> str:
    return f"{company_name} — Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"


def temperature_log_report(company_name: str, rows: list[dict]) -> bytes:
    table_rows = [
        [r["unit_name"], r["unit_type"], f"{r['temperature']}°C",
         "OK" if r["within_limits"] else "OUT OF RANGE", r["recorded_at"]]
        for r in rows
    ]
    elements = [_table(["Unit", "Type", "Temp", "Status", "Recorded At"], table_rows)]
    return _build_pdf("Temperature Log Report", _generated_line(company_name), elements)


def inspection_report(company_name: str, checklist: dict) -> bytes:
    elements = [
        Paragraph(f"Checklist: {checklist['template_name']} ({checklist['category']})", H2_STYLE),
        Paragraph(f"Facility: {checklist.get('facility_name', 'N/A')} | Inspector: "
                   f"{checklist.get('inspector_name', 'N/A')} | Score: {checklist.get('score', 'N/A')}%",
                   SUBTITLE_STYLE),
        Spacer(1, 0.4 * cm),
        _table(
            ["Question", "Result", "Comment"],
            [[i["question"], (i["result"] or "").upper(), i.get("comment") or ""] for i in checklist["items"]],
        ),
    ]
    return _build_pdf("Daily Inspection Report", _generated_line(company_name), elements)


def haccp_monitoring_report(company_name: str, plan_name: str, rows: list[dict]) -> bytes:
    table_rows = [
        [r["ccp_number"], r["ccp_name"], f"{r['measured_value']} {r.get('unit') or ''}",
         "OK" if r["within_limits"] else "DEVIATION", r["recorded_at"]]
        for r in rows
    ]
    elements = [
        Paragraph(f"HACCP Plan: {plan_name}", H2_STYLE),
        _table(["CCP", "Name", "Value", "Status", "Recorded At"], table_rows),
    ]
    return _build_pdf("HACCP Monitoring Report", _generated_line(company_name), elements)


def corrective_actions_report(company_name: str, rows: list[dict]) -> bytes:
    table_rows = [
        [r["title"], r["status"].upper(), r.get("responsible_name") or "Unassigned",
         str(r.get("deadline") or ""), r.get("source") or ""]
        for r in rows
    ]
    elements = [_table(["Title", "Status", "Responsible", "Deadline", "Source"], table_rows)]
    return _build_pdf("Corrective Actions Report", _generated_line(company_name), elements)


def audit_report(company_name: str, audit: dict) -> bytes:
    elements = [
        Paragraph(f"Audit: {audit['title']} ({audit['audit_type']})", H2_STYLE),
        Paragraph(f"Standard: {audit.get('standard') or 'N/A'} | Status: {audit['status']} | "
                   f"Score: {audit.get('score', 'N/A')}", SUBTITLE_STYLE),
        Spacer(1, 0.3 * cm),
        Paragraph(audit.get("summary") or "No summary provided.", styles["Normal"]),
        Spacer(1, 0.4 * cm),
        _table(
            ["Clause", "Severity", "Description", "Status"],
            [[f.get("clause") or "", f["severity"].upper(), f["description"], f["status"]]
             for f in audit.get("findings", [])],
        ),
    ]
    return _build_pdf("Audit Report", _generated_line(company_name), elements)


def compliance_summary_report(company_name: str, summary: dict) -> bytes:
    elements = [
        Paragraph(f"Overall Compliance Score: {summary['compliance_score']}%", H2_STYLE),
        _table(
            ["Metric", "Value"],
            [
                ["Open Corrective Actions", str(summary["open_corrective_actions"])],
                ["Overdue Corrective Actions", str(summary["overdue_corrective_actions"])],
                ["Temperature Alerts (today)", str(summary["temperature_alerts_today"])],
                ["Upcoming Audits", str(len(summary["upcoming_audits"]))],
                ["Recent Inspections", str(len(summary["recent_inspections"]))],
            ],
        ),
    ]
    return _build_pdf("Compliance Summary", _generated_line(company_name), elements)
