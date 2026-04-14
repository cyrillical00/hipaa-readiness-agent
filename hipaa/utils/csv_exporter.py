"""CSV export utilities for assessments and roadmaps."""
import pandas as pd
import io
from datetime import date


def export_assessment_csv(
    readiness: dict, controls: list[dict], org_name: str
) -> bytes:
    """Export full control assessment to CSV."""
    ctrl_map = {c["id"]: c for c in controls}
    rows = []

    for ctrl_id, result in readiness.get("control_results", {}).items():
        c = ctrl_map.get(ctrl_id, {})
        rows.append({
            "Control ID": ctrl_id,
            "Safeguard": c.get("safeguard", ""),
            "Standard": c.get("standard", ""),
            "Specification": c.get("spec", ""),
            "Required/Addressable": c.get("status", ""),
            "Current Status": result.get("status", ""),
            "Score": result.get("score", 0),
            "Gap Tier": result.get("gap_tier", ""),
            "Evidence Present": result.get("evidence", False),
            "Notes": result.get("notes", ""),
            "Remediation Effort": c.get("remediation_effort", ""),
            "Remediation Impact": c.get("remediation_impact", ""),
            "SOC2 Overlap": ", ".join(c.get("soc2_overlap", [])),
        })

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def export_roadmap_csv(roadmap: dict) -> bytes:
    """Export roadmap action items as Jira-importable CSV."""
    rows = []
    for phase in roadmap.get("phases", []):
        phase_label = phase.get("label", f"Phase {phase.get('phase', '?')}")
        for item in phase.get("items", []):
            rows.append({
                "Summary": item.get("title", ""),
                "Description": item.get("description", ""),
                "Priority": item.get("priority", "Medium"),
                "Estimate": item.get("effort", "M"),
                "Labels": f"HIPAA,{phase_label.replace(' ', '_')},{item.get('control_id', '')}",
                "Assignee Role": item.get("owner_role", ""),
                "Phase": phase_label,
                "Control ID": item.get("control_id", ""),
                "Expected Artifact": item.get("expected_artifact", ""),
                "SOC2 Reuse": item.get("soc2_reuse", False),
                "SOC2 Note": item.get("soc2_note", ""),
                "Reported Date": date.today().isoformat(),
            })

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def export_baa_csv(baas: list[dict]) -> bytes:
    """Export BAA inventory to CSV."""
    rows = []
    for baa in baas:
        rows.append({
            "Vendor": baa.get("vendor", ""),
            "Services": baa.get("services", ""),
            "ePHI Shared": baa.get("ephi_shared", False),
            "BAA in Place": baa.get("baa_in_place", False),
            "BAA Signed Date": baa.get("baa_signed_date", ""),
            "BAA Review Date": baa.get("baa_review_date", ""),
            "Sub-BAs Disclosed": baa.get("sub_bas_disclosed", False),
            "Security Incident Clause": baa.get("security_incident_clause", False),
            "Breach Notification Window": baa.get("breach_notification_window", "not specified"),
            "Risk Tier": baa.get("risk_tier", ""),
            "Days Until Review": baa.get("days_until_review", ""),
            "Notes": baa.get("notes", ""),
        })

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
