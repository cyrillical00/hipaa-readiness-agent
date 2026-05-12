"""
BAA inventory risk classification logic.
"""
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "data" / "baa_templates"


RISK_COLORS = {
    "CRITICAL": "#DC2626",
    "HIGH": "#F97316",
    "MEDIUM": "#EAB308",
    "LOW": "#22C55E",
}

RISK_BADGES = {
    "CRITICAL": "🔴 CRITICAL",
    "HIGH": "🟠 HIGH",
    "MEDIUM": "🟡 MEDIUM",
    "LOW": "🟢 LOW",
}


def classify_baa_risk(vendor: dict) -> str:
    """
    Risk classification rules:
    - CRITICAL: ePHI shared + no BAA
    - HIGH: BAA in place but expired, OR no breach clause
    - MEDIUM: BAA complete but sub-BAs not disclosed
    - LOW: Fully compliant
    """
    ephi = vendor.get("ephi_shared", False)
    baa = vendor.get("baa_in_place", False)
    review_date_str = vendor.get("baa_review_date")
    sub_bas = vendor.get("sub_bas_disclosed", False)
    breach_clause = vendor.get("security_incident_clause", False)

    if not ephi:
        return "LOW"

    if ephi and not baa:
        return "CRITICAL"

    # Check expiry
    expired = False
    expiring_soon = False
    if review_date_str:
        try:
            review_date = datetime.strptime(review_date_str, "%Y-%m-%d").date()
            today = date.today()
            if review_date < today:
                expired = True
            elif review_date <= today + timedelta(days=90):
                expiring_soon = True
        except ValueError:
            pass

    if expired:
        return "HIGH"

    if not breach_clause:
        return "HIGH"

    if not sub_bas:
        return "MEDIUM"

    if expiring_soon:
        return "MEDIUM"

    return "LOW"


def enrich_baa_list(baas: list[dict]) -> list[dict]:
    """Add risk_tier and days_until_review to each BAA entry."""
    enriched = []
    today = date.today()
    for baa in baas:
        entry = dict(baa)
        entry["risk_tier"] = classify_baa_risk(baa)
        entry["risk_color"] = RISK_COLORS[entry["risk_tier"]]
        entry["risk_badge"] = RISK_BADGES[entry["risk_tier"]]

        review_str = baa.get("baa_review_date")
        if review_str:
            try:
                review_date = datetime.strptime(review_str, "%Y-%m-%d").date()
                entry["days_until_review"] = (review_date - today).days
            except ValueError:
                entry["days_until_review"] = None
        else:
            entry["days_until_review"] = None

        enriched.append(entry)
    return enriched


def baa_summary(enriched_baas: list[dict]) -> dict:
    """Compute summary metrics for BAA dashboard row."""
    total = len(enriched_baas)
    ephi_vendors = [b for b in enriched_baas if b.get("ephi_shared")]
    missing = len([b for b in ephi_vendors if not b.get("baa_in_place")])
    critical = len([b for b in enriched_baas if b["risk_tier"] == "CRITICAL"])
    high = len([b for b in enriched_baas if b["risk_tier"] == "HIGH"])
    expiring_90d = len([
        b for b in enriched_baas
        if b.get("days_until_review") is not None and 0 <= b["days_until_review"] <= 90
    ])
    expired = len([
        b for b in enriched_baas
        if b.get("days_until_review") is not None and b["days_until_review"] < 0
    ])

    return {
        "total": total,
        "ephi_vendors": len(ephi_vendors),
        "missing_baas": missing,
        "expiring_90d": expiring_90d,
        "expired": expired,
        "critical": critical,
        "high": high,
        "compliance_rate": round(
            (len(ephi_vendors) - missing) / len(ephi_vendors) * 100 if ephi_vendors else 100, 1
        ),
    }


def list_templates() -> list[dict]:
    """Returns [{key, name, path, body}, ...] for every .md file in baa_templates/."""
    if not TEMPLATES_DIR.exists():
        return []
    out = []
    for p in sorted(TEMPLATES_DIR.glob("*.md")):
        out.append({
            "key": p.stem,
            "name": p.stem.replace("_", " ").title(),
            "path": str(p),
            "body": p.read_text(encoding="utf-8"),
        })
    return out


def fill_template(template_body: str, fields: dict) -> str:
    """Substitute {curly_brace} fields. Missing keys leave the placeholder intact."""
    out = template_body
    for k, v in fields.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def draft_outreach_email(
    vendor_name: str,
    risk_tier: str,
    ephi_scope: str,
    requester_org: str,
    requester_name: str,
    template_key: str = "saas_vendor",
) -> str:
    """Refines a starter template into a vendor-specific draft via Haiku.

    Falls back to the deterministic filled template when Claude is unavailable
    so the page still functions without an API key.
    """
    from engine.claude_client import ClaudeWrapper

    templates = {t["key"]: t for t in list_templates()}
    base = templates.get(template_key) or templates.get("saas_vendor")
    if not base:
        return "No templates available."

    seed = fill_template(base["body"], {
        "vendor_name": vendor_name,
        "risk_tier": risk_tier,
        "ephi_scope": ephi_scope,
        "requester_org": requester_org,
        "requester_name": requester_name,
        "service_description": "your service",
        "target_weeks": "4",
    })

    system_prompt = (
        "You are a HIPAA compliance officer drafting outreach emails to vendors "
        "that need a Business Associate Agreement. You receive a starter draft "
        "and adapt it to be specific, professional, and concise. Keep CFR "
        "citations and the structure intact. Reply with the email body only, "
        "no JSON, no markdown fences, no preamble. Never use em dash characters; "
        "use commas, semicolons, or rewrite the sentence."
    )
    user_prompt = (
        f"Vendor: {vendor_name}\n"
        f"Their service for us: {ephi_scope}\n"
        f"Risk tier: {risk_tier}\n\n"
        f"Starter draft:\n___\n{seed}\n___\n\n"
        f"Refine into a final email body. Be specific about why this vendor "
        f"needs a BAA given their service. Keep it under 250 words."
    )

    try:
        wrapper = ClaudeWrapper(model="claude-haiku-4-5-20251001")
        json_system = (
            system_prompt
            + ' Wrap your output as JSON: {"body": "<email body>"}.'
        )
        parsed, _usage = wrapper.stream_json(
            json_system, user_prompt, max_tokens=1500,
            progress_label="baa_outreach_draft",
        )
        return parsed.get("body", seed)
    except Exception:
        return seed
